from PyQt5.QtWidgets import QApplication, QTextEdit
from PyQt5.QtGui import QFont
import sys

app = QApplication(sys.argv)

text_edit = QTextEdit()
text_edit.setFont(QFont("Microsoft YaHei", 14))  # 中文字体
text_edit.setFocus()
text_edit.setPlainText("这是中文测试文本。\nHello，世界！")
text_edit.show()

sys.exit(app.exec_())