from openai import OpenAI
import os


def transcribe_audio(audio_path: str, model_size: str = None, language: str = "ko") -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=f,
            language="ko",
            response_format="verbose_json",
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

    # verbose_json → SRT 형식으로 변환
    srt_lines = []
    for i, seg in enumerate(response.segments, 1):
        start = _seconds_to_srt(seg.start)
        end = _seconds_to_srt(seg.end)
        srt_lines.append(f"{i}\n{start} --> {end}\n{seg.text.strip()}\n")

    return "\n".join(srt_lines)


def _seconds_to_srt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
