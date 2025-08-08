from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import PathPatch
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QComboBox, QFileDialog, QMessageBox
)
class PreviewWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Text Path Preview (G-code will follow this path)")
        self.resize(600, 600)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # self.draw_path(text_path)

    def draw_path(self, text_path):
        self.figure.clf()
        ax = self.figure.add_subplot(111)
        patch = PathPatch(text_path, facecolor='black', edgecolor='black', lw=1)
        ax.add_patch(patch)

        ax.set_xlim(text_path.vertices[:, 0].min() - 10, text_path.vertices[:, 0].max() + 10)
        ax.set_ylim(text_path.vertices[:, 1].min() - 10, text_path.vertices[:, 1].max() + 10)
        ax.set_aspect('equal')
        # ax.invert_yaxis()  # CNC 视角通常是向下为正
        ax.grid(True)
        self.canvas.draw()