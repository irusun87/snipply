from openai import OpenAI
import os
import subprocess
from pathlib import Path


def _compress_audio(audio_path: str) -> str:
    """25MB 초과 시 ffmpeg으로 압축"""
    size_mb = Path(audio_path).stat().st_size / (1024 * 1024)
    if size_mb <= 24:
        return audio_path

    compressed_path = "/tmp/snipply_compressed.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-i", audio_path,
        "-ar", "16000",      # 샘플레이트 낮춤
        "-ac", "1",          # 모노
        "-b:a", "32k",       # 비트레이트 낮춤
        compressed_path
    ], capture_output=True)

    return compressed_path


def transcribe_audio(audio_path: str, model_size: str = None, language: str = "ko") -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # 25MB 초과 시 자동 압축
    audio_path = _compress_audio(audio_path)

    with open(audio_path, "rb") as f:
        srt_raw = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="ko",
            response_format="srt",
            prompt=(
                "한국어 유튜브 예능/군대 콘텐츠 전사입니다. "
                "군대 관련 용어(병장, 이병, 해병대, UDT, 특전사, 전역, 복무, 훈련소 등)와 "
                "연예인 이름, 방송 프로그램명을 정확하게 인식해주세요. "
                "발화자가 여러 명인 경우 대화체로 자연스럽게 전사하고, "
                "군대 은어나 줄임말도 맥락에 맞게 처리해주세요. "
                "말끝 흐림(~, ...) 이나 웃음소리(ㅋㅋ, 하하)는 제거하고 "
                "발화 내용만 깔끔하게 전사해주세요."
            )
        )

    return srt_raw.strip()
