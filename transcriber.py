from openai import OpenAI
import os
import subprocess
from pathlib import Path


def _compress_audio(audio_path: str) -> str:
    """무조건 16kHz 모노 mp3로 압축 (Whisper 최적화)"""
    compressed_path = "/tmp/snipply_compressed.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-i", audio_path,
        "-ar", "16000",
        "-ac", "1",
        "-b:a", "32k",
        compressed_path
    ], capture_output=True)
    return compressed_path


def transcribe_audio(audio_path: str, model_size: str = None, language: str = "ko") -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # 무조건 압축 (13분 영상도 약 3~4MB로 줄어듦)
    compressed_path = _compress_audio(audio_path)

    # 압축 후에도 25MB 초과 시 청크 분할 전사
    size_mb = Path(compressed_path).stat().st_size / (1024 * 1024)

    if size_mb <= 24:
        with open(compressed_path, "rb") as f:
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

    else:
        # 25MB 초과 시 10분씩 청크 분할
        return _transcribe_chunks(client, compressed_path)


def _transcribe_chunks(client, audio_path: str) -> str:
    """긴 파일을 10분씩 분할해서 전사"""
    chunk_dir = "/tmp/snipply_chunks"
    os.makedirs(chunk_dir, exist_ok=True)

    # 10분(600초)씩 분할
    subprocess.run([
        "ffmpeg", "-y", "-i", audio_path,
        "-f", "segment",
        "-segment_time", "600",
        "-c", "copy",
        f"{chunk_dir}/chunk_%03d.mp3"
    ], capture_output=True)

    chunks = sorted(Path(chunk_dir).glob("chunk_*.mp3"))
    all_srt = []
    offset_seconds = 0

    for chunk in chunks:
        with open(chunk, "rb") as f:
            srt = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="ko",
                response_format="srt",
                prompt="한국어 유튜브 콘텐츠 전사입니다."
            )

        # 타임라인에 offset 더하기
        adjusted = _adjust_srt_offset(srt, offset_seconds)
        all_srt.append(adjusted)

        # 다음 청크 offset 계산 (10분)
        offset_seconds += 600

    return "\n\n".join(all_srt)


def _adjust_srt_offset(srt_text: str, offset_seconds: int) -> str:
    """SRT 타임라인에 offset 추가"""
    import re

    def add_offset(match):
        def to_seconds(h, m, s, ms):
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

        def to_srt_time(total_seconds):
            ms = int((total_seconds % 1) * 1000)
            total = int(total_seconds)
            h = total // 3600
            m = (total % 3600) // 60
            s = total % 60
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        start = to_seconds(match.group(1), match.group(2), match.group(3), match.group(4))
        end = to_seconds(match.group(5), match.group(6), match.group(7), match.group(8))
        return f"{to_srt_time(start + offset_seconds)} --> {to_srt_time(end + offset_seconds)}"

    pattern = r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})'
    return re.sub(pattern, add_offset, srt_text)
