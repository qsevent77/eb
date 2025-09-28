import matplotlib.pyplot as plt

def plot_unipen_trajectory(file_path, invert_y=False, show=True):
    """
    绘制 UNIPEN 输出的笔迹路径文件（output_rawxy / output_namedxy 格式）。

    参数:
        file_path (str): 笔迹路径文件路径
        invert_y (bool): 是否翻转 Y 轴（UNIPEN 坐标原点在左上角）
        show (bool): 是否立即显示图像
    """
    with open(file_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 分离标签和坐标
        parts = line.split()
        label = parts[0]  # 标签
        coords = parts[1:]
        
        # 将坐标转换为浮点数
        xs = [float(coords[i]) for i in range(0, len(coords), 2)]
        ys = [float(coords[i+1]) for i in range(0, len(coords), 2)]
        
        # 绘制轨迹
        plt.figure(figsize=(6,6))
        plt.plot(xs, ys)
        plt.title(label)
        if invert_y:
            plt.gca().invert_yaxis()
        plt.axis('equal')
        if show:
            plt.show()

# 使用示例
plot_unipen_trajectory("unipen/statis/a_samples.txt")
