from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
from scipy.ndimage import convolve
from skimage.morphology import skeletonize as sk_skeletonize
from fontTools.ttLib import TTFont
import turtle
import time
import os
from tqdm import tqdm

def render_char_to_bitmap(font_path, char, img_size=256, font_number=0):
    img = Image.new("L", (img_size, img_size), 0)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, size=img_size-20, index=font_number)
    bbox = draw.textbbox((0,0), char, font=font)
    w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text(((img_size-w)/2 - bbox[0], (img_size-h)/2 - bbox[1]), char, font=font, fill=255)
    return np.array(img)


def skeletonize(img):
    _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    skeleton = np.zeros(binary.shape, np.uint8)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
    size = np.size(binary)
    done = False
    m = "data"
    x = 0
    while not done:
        eroded = cv2.erode(binary, element)
        Image.fromarray(eroded).save(f"{m}/eroded_{str(x)}.png")
        temp = cv2.dilate(eroded, element)
        Image.fromarray(temp).save(f"{m}/temp1_{str(x)}.png")
        temp = cv2.subtract(binary, temp)
        Image.fromarray(temp).save(f"{m}/temp2_{str(x)}.png")
        skeleton = cv2.bitwise_or(skeleton, temp)
        Image.fromarray(skeleton).save(f"{m}/skeleton_{str(x)}.png")
        binary = eroded.copy()
        zeros = size - cv2.countNonZero(binary)
        if zeros == size:
            done = True
        x += 1
    return skeleton

def skeleton_to_trace(skel_img):
    """
    skeleton_img: 二值骨架图 (255=骨架)
    输出: trace_list = [(x, y, pen_state), ...]
    """
    skel = skel_img.copy()
    skel[skel > 0] = 1  # 0/1
    h, w = skel.shape
    trace_list = []

    # 找轮廓，轮廓本身是笔画的一条路径
    contours, _ = cv2.findContours(skel.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    for cnt in contours:
        # 抬笔
        trace_list.append((cnt[0][0][0], cnt[0][0][1], 0))
        for point in cnt:
            x, y = point[0]
            trace_list.append((x, y, 1))  # 笔触
        # 最后抬笔
        trace_list.append((cnt[-1][0][0], cnt[-1][0][1], 0))

    return trace_list

def draw_trace(trace, img_size=256, screen_size=500, delay=0.002):
    """
    trace: [(x, y, pen_state), ...]  x, y是像素坐标
    img_size: 原始图像尺寸（像素）
    screen_size: Turtle窗口尺寸
    delay: 每步动画时间间隔
    """
    # Turtle 初始化
    t = turtle.Turtle()
    t.hideturtle()
    t.speed(0)
    t.penup()

    screen = turtle.Screen()
    screen.setup(screen_size, screen_size)
    screen.title("Trace Animation")

    # 坐标归一化到 Turtle 窗口坐标 (-screen_size/2 ~ screen_size/2)
    scale = screen_size / img_size
    offset = screen_size / 2

    for x, y, pen_state in trace:
        tx = x * scale - offset
        ty = offset - y * scale  # y 轴反向
        if pen_state == 0:
            t.penup()
            t.goto(tx, ty)
        else:
            t.pendown()
            t.goto(tx, ty)
        time.sleep(delay)

    screen.mainloop()

def safe_skeletonize(img, threshold=50, min_area=1):
    """
    完整安全骨架提取函数
    输入灰度图或彩色图，输出单像素宽骨架并去除孤立噪点。

    参数:
        img : np.ndarray
            输入图像（灰度或彩色）
        threshold : int
            二值化阈值（0-255）
        min_area : int
            保留连通域最小面积，孤立像素会被去掉

    返回:
        clean_skel : np.ndarray
            单通道 uint8 骨架图像，0 背景，255 骨架
    """
    # 1. 转灰度
    if len(img.shape) == 3:
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        img_gray = img.copy()

    # 2. 二值化
    _, binary = cv2.threshold(img_gray, threshold, 255, cv2.THRESH_BINARY)
    binary_bool = binary > 0  # skimage skeletonize 需要布尔型

    # 3. 提取骨架
    skeleton = sk_skeletonize(binary_bool)
    skeleton = (skeleton.astype(np.uint8)) * 255  # 转回 uint8

    # 4. 删除孤立小连通域
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(skeleton)
    clean_skel = np.zeros_like(skeleton)
    for i in range(1, num_labels):  # 跳过背景
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            clean_skel[labels == i] = 255

    return clean_skel

def remove_short_branches_any_dir(skel, min_length=10):
    """
    skel: uint8 0/255 单像素骨架
    min_length: 小于这个长度的支线会被删除
    """
    skel = skel.copy() // 255
    skel_out = skel.copy()
    
    # 8邻域卷积，用于检测端点
    kernel = np.ones((3,3), dtype=int)
    kernel[1,1] = 0
    neighbor_count = convolve(skel, kernel, mode='constant', cval=0)
    
    # 端点坐标
    endpoints = np.array(np.where((neighbor_count==1) & (skel==1))).T

    visited = np.zeros_like(skel, dtype=bool)
    
    def trace(y,x):
        path = [(y,x)]
        py, px = y, x
        prev = None
        while True:
            visited[py,px] = True
            # 找未访问的邻居
            neighbors = []
            for dy in [-1,0,1]:
                for dx in [-1,0,1]:
                    ny, nx = py+dy, px+dx
                    if 0<=ny<skel.shape[0] and 0<=nx<skel.shape[1]:
                        if skel[ny,nx]==1 and not visited[ny,nx]:
                            neighbors.append((ny,nx))
            if len(neighbors)==0 or len(neighbors)>1:
                break  # 到达端点或分叉
            py, px = neighbors[0]
            path.append((py, px))
        return path

    for y, x in endpoints:
        if visited[y,x]:
            continue
        path = trace(y,x)
        if len(path) < min_length:
            for py, px in path:
                skel_out[py, px] = 0
                visited[py, px] = True

    return (skel_out*255).astype(np.uint8)

def get_font_chars(font_path, font_number=0):
    """
    获取字体文件中所有可用字符
    支持 TTF/TTC
    """
    chars = []
    try:
        # 打开 TTF/TTC
        tt = TTFont(font_path, fontNumber=font_number)
        # cmap 表包含字符编码
        for table in tt['cmap'].tables:
            if table.isUnicode():
                chars.extend(table.cmap.keys())
        # 转为字符
        chars = [chr(c) for c in chars]
        chars = list(set(chars))  # 去重
    except Exception as e:
        print(f"Error reading font {font_path}: {e}")
    return chars

def run(font_path, img_size=256, font_number=0, save_dir=None):
    """
    遍历字体里的字符，把每个字符渲染成图像
    """
    chars = get_font_chars(font_path, font_number)
    for c in tqdm(chars, desc="Processing characters"):
        try:
            bitmap = render_char_to_bitmap(font_path, c, img_size, font_number)
            skel = safe_skeletonize(bitmap)
            skel = remove_short_branches_any_dir(skel,15)
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)
                skel_dir = os.path.join(save_dir, "skeleton")
                img_dir = os.path.join(save_dir, "glyph")
                os.makedirs(skel_dir, exist_ok=True)
                os.makedirs(img_dir, exist_ok=True)
                char_safe = c
                for ch in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
                    char_safe = char_safe.replace(ch, '_')
                fname = f"{char_safe}_glyph.png"
                skelf = f"{char_safe}_skeleton.png"
                Image.fromarray(bitmap).save(os.path.join(img_dir, fname))
                Image.fromarray(skel).save(os.path.join(skel_dir, skelf))
        except Exception as e:
            print(f"Failed to render char {c}: {e}")


# ========== 测试 ==========
if __name__ == "__main__":
    font_path = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
    run(font_path, img_size=256, font_number=0, save_dir="data/font_chars")