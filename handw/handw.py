import tkinter as tk
from tkinter import filedialog, font, ttk, messagebox
from docx import Document
import matplotlib.pyplot as plt
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from control import text_to_gcode, preview_text_path, export_gcode_to_file, get_font_support
import utils as ul
import os
from functools import partial

def load_text_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("Word Documents", "*.docx")])
    if not file_path:
        return

    text_content = ""
    if file_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            text_content = f.read()
    elif file_path.endswith(".docx"):
        doc = Document(file_path)
        text_content = "\n".join([para.text for para in doc.paragraphs])

    text_widget.delete(1.0, tk.END)
    text_widget.insert(tk.END, text_content)

def change_font(event=None):
    selected_font = font_box.get()
    # text_widget.configure(font=(selected_font, 14))

def preview_text(text_widget):
    text = text_widget.get(1.0, tk.END).rstrip()
    if not text:
        messagebox.showwarning("Warning", "Text area is empty!")
        return
    font_name = font_box.get()
    font_file = get_font_support().get(font_name)
    gcode, text_path = text_to_gcode(text, font_name=font_file)
    preview_text_path(text_path)

def export_gcode():
    text = text_widget.get(1.0, tk.END).rstrip()
    if not text:
        messagebox.showwarning("Warning", "Text area is empty!")
        return
    font_name = font_box.get()
    font_file = get_font_support().get(font_name)
    gcode, _ = text_to_gcode(text, font_name=font_file)

    filename = filedialog.asksaveasfilename(defaultextension=".gcode", filetypes=[("G-code Files", "*.gcode")])
    if not filename:
        return
    export_gcode_to_file(gcode, filename)
    messagebox.showinfo("Success", f"G-code saved to {filename}")

# =================== GUI ===================
root = tk.Tk()
root.title("写字机 G-code 生成器")

frame_top = ttk.Frame(root)
frame_top.pack(fill="x", padx=10, pady=5)

btn_load = ttk.Button(frame_top, text="open files", command=load_text_file)
btn_load.pack(side="left")

font_box = ttk.Combobox(frame_top, values=list(get_font_support().keys()), state="readonly")
font_box.set("DejaVuSans")
font_box.pack(side="left", padx=10)
font_box.bind("<<ComboboxSelected>>", change_font)

btn_export = ttk.Button(frame_top, text="Gen G-code", command=export_gcode)
btn_export.pack(side="right")

text_widget = tk.Text(root, wrap="word", font=("Arial", 14), height=20)
text_widget.pack(fill="both", expand=True, padx=10, pady=5)

btn_preview = ttk.Button(frame_top, text="preview G-code", command=partial(preview_text, text_widget))
btn_preview.pack(side="left")

root.mainloop()


