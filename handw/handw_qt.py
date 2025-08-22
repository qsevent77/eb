import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QComboBox, QFileDialog, QMessageBox,
    QLabel, QLineEdit
)
from docx import Document 
from control import text_to_gcode, export_gcode_to_file, get_font_support, upload_gcode_to_grbl
from qt_show import PreviewWindow
import serial
import serial.tools.list_ports

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

        serial_layout = QHBoxLayout()
        serial_layout.setSpacing(5)
        label_port = QLabel("Port:")
        label_port.setMaximumWidth(40)  # 限制最大宽度，适当调节数字
        serial_layout.addWidget(label_port)
        self.port_box = QComboBox()
        self.port_box.setFixedWidth(145)
        self.refresh_ports()
        serial_layout.addWidget(self.port_box)

        label_baudrate = QLabel("Baudrate:")
        label_baudrate.setMaximumWidth(70)  # 限制最大宽度，适当调节数字
        serial_layout.addWidget(label_baudrate)
        self.baudrate_box = QComboBox()
        self.baudrate_box.setFixedWidth(115)
        self.baudrate_box.addItems(["9600", "115200", "250000"])
        self.baudrate_box.setCurrentText("115200")
        serial_layout.addWidget(self.baudrate_box)

        label_empty = QLabel()
        label_empty.setMaximumWidth(220)  # 限制最大宽度，适当调节数字
        serial_layout.addWidget(label_empty)

        btn_upload = QPushButton("Upload to GRBL")
        btn_upload.clicked.connect(self.upload_to_grbl)
        serial_layout.addWidget(btn_upload)

        main_layout.addLayout(serial_layout)

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
            "Text and Word Files (*.txt *.docx);;Text Files (*.txt);;Word Documents (*.docx)"
        )

        if not file_path:
            return

        text_content = ""
        if file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                text_content = f.read()
            self.text_widget.setPlainText(text_content)
        elif file_path.endswith(".docx"):
            # doc = Document(file_path)
            # text_content = "\n".join([para.text for para in doc.paragraphs])
            import mammoth
            with open(file_path, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                html = result.value  # 转换后html字符串
            self.text_widget.setHtml(html)

        # self.text_widget.setPlainText(text_content)

    def change_font(self, font_name):
        selected_font = font_name or self.font_box.currentText()
        self.text_widget.setFontFamily(selected_font)

    def generate_gode(self):
        text = self.text_widget.toPlainText().rstrip()
        if not text:
            QMessageBox.warning(self, "Warning", "Text area is empty!")
            return

        font_name = self.font_box.currentText()
        font_file = get_font_support().get(font_name)

        gcode, text_path = text_to_gcode(text, font_name=font_file)
        return gcode, text_path

    def export_gcode(self):
        gcode, _  = self.generate_gode()

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
        _, text_path = self.generate_gode()
        self.preview_window.draw_path(text_path)
        self.preview_window.show()

    def refresh_ports(self):
        self.port_box.clear()
        ports = [p.device for p in serial.tools.list_ports.comports()]
        if not ports:
            ports = ["No Ports Found"]
        self.port_box.addItems(ports)

    def upload_to_grbl(self):
        port = self.port_box.currentText().strip()
        baudrate = int(self.baudrate_box.currentText().strip())
        gcode, _  = self.generate_gode()

        if not gcode.strip():
            QMessageBox.warning(self, "Warning", "G-code is empty!")
            return
        try:
            upload_gcode_to_grbl(port, baudrate, gcode, is_file=False)
            QMessageBox.information(self, "Success", "G-code uploaded successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to upload G-code:\n{e}")

def main():
    app = QApplication(sys.argv)
    window = GCodeGenerator()
    window.resize(800, 300)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()