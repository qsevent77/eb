import matplotlib.pyplot as plt
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from matplotlib.patches import PathPatch
from matplotlib.path import Path
import numpy as np
import utils as ul
import os
import serial
import time
from typing import Union

def multiline_text_path(text, font_size=20, font_name="DejaVu Sans"):
    # font_prop = FontProperties(family=font_name)
    font_prop = FontProperties(fname=font_name)
    lines = text.split("\n")
    line_spacing = font_size * 1.2

    paths = []
    for i, line in enumerate(lines):
        y_offset = -i * line_spacing
        path = TextPath((0, y_offset), line, size=font_size, prop=font_prop)
        paths.append(path)

    all_vertices = np.concatenate([p.vertices for p in paths])
    all_codes = np.concatenate([p.codes for p in paths])
    return Path(all_vertices, all_codes)

def text_to_gcode(text, font_size=20, font_name="DejaVu Sans", feedrate=1000, z_safe=5, z_draw=-1):
    text_path = multiline_text_path(text, font_size, font_name)

    vertices = text_path.vertices
    codes = text_path.codes

    gcode = []
    gcode.append("G21 ; 设置单位为毫米")
    gcode.append("G90 ; 使用绝对坐标")
    gcode.append(f"G1 F{feedrate} ; 设置进给速度")

    pen_down = False
    for code, (x, y) in zip(codes, vertices):
        if code == 1:  # MOVETO
            if pen_down:
                gcode.append(f"G0 Z{z_safe}")
                pen_down = False
            gcode.append(f"G0 X{x:.3f} Y{y:.3f}")
            gcode.append(f"G1 Z{z_draw}")
            pen_down = True
        elif code == 2:  # LINETO
            gcode.append(f"G1 X{x:.3f} Y{y:.3f}")
        elif code == 79:  # CLOSEPOLY
            if pen_down:
                gcode.append(f"G0 Z{z_safe}")
                pen_down = False

    if pen_down:
        gcode.append(f"G0 Z{z_safe}")

    gcode.append("M2 ; 程序结束")
    return "\n".join(gcode), text_path

def preview_text_path(text_path):
    fig, ax = plt.subplots()
    patch = PathPatch(text_path, facecolor='black', edgecolor='black', lw=1)
    ax.add_patch(patch)

    ax.set_xlim(text_path.vertices[:, 0].min() - 10, text_path.vertices[:, 0].max() + 10)
    ax.set_ylim(text_path.vertices[:, 1].min() - 10, text_path.vertices[:, 1].max() + 10)
    ax.set_aspect('equal')
    ax.invert_yaxis()  # CNC 视角通常是向下为正
    ax.set_title("Text Path Preview (G-code will follow this path)")
    plt.grid(True)
    plt.show()


def list_fonts():
    import matplotlib.font_manager as fm
    return fm.findSystemFonts(fontpaths=None, fontext='ttf')


def export_gcode_to_file(gcode, filename):
    with open(filename, 'w') as f:
        f.write(gcode)
    print(f"G-code saved to {filename}")

def system_fonts():
    sys_fonts = {
        "DejaVuSans": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "wqy-zenhei": "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "NotoSansCJK-Regular": "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    }
    return sys_fonts

def get_font_support():
    hw_font_dir = ""  # your font
    files = ul.list_file(hw_font_dir, suffixes=['.ttf', '.ttc'])
    fonts = {os.path.basename(file).split('.')[0]:file for file in files}
    sys_fonts = system_fonts()
    fonts.update(sys_fonts)
    return fonts


def upload_gcode_to_grbl(port: str, baudrate: int, gcode: Union[str, list], is_file: bool = True):
    """
    上传 G-code 到 GRBL 控制板
    
    参数:
        port (str): 串口端口 (Windows: 'COM3', Linux: '/dev/ttyUSB0')
        baudrate (int): 波特率 (GRBL 默认 115200)
        gcode (str|list): G-code 文件路径 (is_file=True) 或 G-code 文本/列表 (is_file=False)
        is_file (bool): True 表示 gcode 是文件路径, False 表示 gcode 是字符串或列表
    """
    # 读取 G-code 内容
    if is_file:
        if not os.path.exists(gcode):
            raise FileNotFoundError(f"G-code file not found: {gcode}")
        with open(gcode, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        if isinstance(gcode, str):
            lines = gcode.splitlines()
        elif isinstance(gcode, list):
            lines = gcode
        else:
            raise ValueError("gcode must be str or list when is_file=False")

    # 连接 GRBL
    ser = serial.Serial(port, baudrate, timeout=1)
    time.sleep(2)  # 等待 GRBL 上电复位

    # 重置并清空缓冲
    ser.write(b"\r\n\r\n")
    time.sleep(2)
    ser.flushInput()

    # 发送 G-code
    for line in lines:
        l = line.strip()
        if not l or l.startswith("("):  # 跳过空行和注释
            continue
        cmd = (l + "\n").encode("utf-8")
        ser.write(cmd)
        print(f"Sent: {l}")
        
        # 等待 GRBL 回复
        while True:
            reply = ser.readline().decode(errors="ignore").strip()
            if reply:
                print(f"Reply: {reply}")
                if reply.lower() == "ok" or reply.lower().startswith("error"):
                    break

    ser.close()
    print("✅ G-code upload complete.")


if __name__ == "__main__":
    get_font_support()
