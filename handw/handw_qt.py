import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QComboBox, QFileDialog, QMessageBox
)
from docx import Document 
from control import text_to_gcode, export_gcode_to_file, get_font_support
from qt_show import PreviewWindow

class GCodeGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("写字机 G-code 生成器")
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()

        self.preview_window = PreviewWindow()
        # open files button
        btn_load = QPushButton("open files")
        btn_load.clicked.connect(self.load_text_file)
        top_layout.addWidget(btn_load)

        # font combobox
        self.font_box = QComboBox()
        self.font_support = get_font_support()
        self.font_box.addItems(self.font_support.keys())
        self.font_box.setCurrentText("DejaVuSans")
        self.font_box.currentTextChanged.connect(self.change_font)
        top_layout.addWidget(self.font_box)

        # preview button
        btn_preview = QPushButton("preview G-code")
        btn_preview.clicked.connect(self.preview_text)
        top_layout.addWidget(btn_preview)

        # gen g-code button
        btn_export = QPushButton("Gen G-code")
        btn_export.clicked.connect(self.export_gcode)
        top_layout.addWidget(btn_export)

        main_layout.addLayout(top_layout)

        # text editor
        self.text_widget = QTextEdit()
        self.text_widget.setFontFamily("Microsoft YaHei")
        self.text_widget.setFontPointSize(14)
        main_layout.addWidget(self.text_widget)

        self.setLayout(main_layout)

    def load_text_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Text Files (*.txt);;Word Documents (*.docx)"
        )

        if not file_path:
            return

        text_content = ""
        if file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                text_content = f.read()
        elif file_path.endswith(".docx"):
            doc = Document(file_path)
            text_content = "\n".join([para.text for para in doc.paragraphs])

        self.text_widget.setPlainText(text_content)

    def change_font(self, font_name):
        selected_font = font_name or self.font_box.currentText()
        self.text_widget.setFontFamily(selected_font)

    def export_gcode(self):
        text = self.text_widget.toPlainText().rstrip()
        if not text:
            QMessageBox.warning(self, "Warning", "Text area is empty!")
            return

        font_name = self.font_box.currentText()
        font_file = get_font_support().get(font_name)

        gcode, _ = text_to_gcode(text, font_name=font_file)

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save G-code File",
            "",
            "G-code Files (*.gcode)"
        )
        if not filename:
            return
        filename = filename + ".gcode"
        export_gcode_to_file(gcode, filename)
        QMessageBox.information(self, "Success", f"G-code saved to:\n{filename}")

    def preview_text(self):
        text = self.text_widget.toPlainText().rstrip()
        if not text:
            QMessageBox.warning(self, "Warning", "Text area is empty!")
            return

        font_name = self.font_box.currentText()
        font_file = get_font_support().get(font_name)
        _, text_path = text_to_gcode(text, font_name=font_file)
        self.preview_window.draw_path(text_path)
        self.preview_window.show()

def main():
    app = QApplication(sys.argv)
    window = GCodeGenerator()
    window.resize(800, 300)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()