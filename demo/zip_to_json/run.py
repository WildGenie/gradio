import gradio as gr
from zipfile import ZipFile

def zip_to_json(file_obj):
    files = []
    with ZipFile(file_obj.name) as zfile:
        files.extend({
                "name": zinfo.filename,
                "file_size": zinfo.file_size,
                "compressed_size": zinfo.compress_size,
            } for zinfo in zfile.infolist())
    return files


iface = gr.Interface(zip_to_json, "file", "json")
if __name__ == "__main__":
    iface.launch()
