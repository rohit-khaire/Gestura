"""Launch the FastAPI sign detector inside a free Hugging Face Gradio Space."""

import sys

import gradio as gr
import uvicorn

sys.path.insert(0, "src")

from api import create_app


api = create_app()

demo = gr.Blocks(title="Fluent Meet Sign Detection API")
with demo:
    gr.Markdown("# Fluent Meet Sign Detection API")
    gr.Markdown("API health: `/health` | Detection endpoint: `/detect`")

app = gr.mount_gradio_app(api, demo, path="/ui")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)