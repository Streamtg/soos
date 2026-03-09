import gradio as gr
from faster_whisper import WhisperModel
import edge_tts
import asyncio

model = WhisperModel("tiny", device="cpu")

async def tts(text):
    out="out.mp3"
    c=edge_tts.Communicate(text,voice="es-ES-AlvaroNeural")
    await c.save(out)
    return out

def transcribe(audio):
    segments,_=model.transcribe(audio)
    text=""
    for s in segments:
        text+=s.text
    return text

with gr.Blocks() as demo:

    gr.Markdown("# SoniTranslate CPU")

    audio=gr.Audio(type="filepath")
    txt=gr.Textbox()

    btn=gr.Button("Transcribir")

    btn.click(transcribe,audio,txt)

demo.launch()
