import subprocess
import tempfile
import os
from pathlib import Path


def download_audio(url: str) -> str:
    """
    yt-dlp으로 YouTube 영상에서 오디오만 추출합니다.
    Returns: 로컬 오디오 파일 경로 (mp3)
    """
    out_dir = Path(tempfile.mkdtemp())
    out_template = str(out_dir / "audio.%(ext)s")

    cmd = [
        "yt-dlp",
        "-x",                          # 오디오만 추출
        "--audio-format", "mp3",       # mp3 변환
        "--audio-quality", "0",        # 최고 품질
        "-o", out_template,
        "--no-playlist",               # 재생목록 제외
        url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp 오류:\n{result.stderr}")

    # 생성된 파일 찾기
    files = list(out_dir.glob("audio.*"))
    if not files:
        raise FileNotFoundError("오디오 파일을 찾을 수 없습니다.")

    return str(files[0])
