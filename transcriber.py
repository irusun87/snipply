from openai import OpenAI
import os

def transcribe_audio(audio_path: str, model_size: str = None, language: str = "ko") -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="ko",
            response_format="text",
            prompt="유튜브 영상 전사입니다. 자연스러운 한국어로 전사해주세요."
        )
    return transcript.strip()
