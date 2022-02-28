import gradio as gr

def greet(name):
  return f"Hello {name}!!"

iface = gr.Interface(fn=greet, inputs="text", outputs="text")
if __name__ == "__main__":
    iface.launch()
