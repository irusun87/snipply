from openai import OpenAI
import os

def transcribe_audio(audio_path: str, model_size: str = None, language: str = "ko") -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="ko",
            response_format="srt",
            prompt="유튜브 영상 전사입니다. 자연스러운 한국어로 전사해주세요."
        )

    return transcript.strip()
```

`response_format="srt"` 로 바꾸면 이렇게 나와요.
```
1
00:00:00,000 --> 00:00:03,000
병장 때 6천 원이었나?

2
00:00:03,500 --> 00:00:07,200
제가 20만 원밖에 받았던 것 같아요
