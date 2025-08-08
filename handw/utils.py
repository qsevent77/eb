import os

def list_file(folder_path, suffixes=None):
    if not isinstance(suffixes, (str, list, tuple, type(None))):
        raise TypeError(f"参数类型错误，必须是 str、list 或 tuple，当前类型是 {type(suffixes).__name__}")
    if isinstance(suffixes, list):
        suffixes = tuple(suffixes)
    font_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if suffixes and file.lower().endswith(suffixes):
                font_files.append(os.path.join(root, file))
            
            if not suffixes:
                font_files.append(os.path.join(root, file))

    return font_files