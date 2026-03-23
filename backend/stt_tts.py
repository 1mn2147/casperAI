import whisper
from gtts import gTTS
import os

# STT: Whisper-large-v3-turbo (Local)
def transcribe_audio(file_path: str) -> str:
    # Use large-v3-turbo model, or default to a smaller one if constrained
    model = whisper.load_model("large-v3-turbo")
    result = model.transcribe(file_path)
    return result["text"]

# TTS: gTTS (Google TTS)
def synthesize_speech(text: str, output_path: str):
    tts = gTTS(text=text, lang='ko')
    tts.save(output_path)
    return output_path
