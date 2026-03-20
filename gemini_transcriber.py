from google import genai
from google.genai import types
import os
import json
import re
import time
import mimetypes
import shutil
from pathlib import Path


def transcribe_with_gemini(audio_path: str, category: str = "감동", shorts_count: int = 3, titles_per_topic: int = 5) -> tuple:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    if category == "감동":
        style_guide = """
나레이션 스타일:
- 장면을 생생하게 묘사, 정중하고 담백한 존댓말(~입니다, ~였습니다)
- 음슴체 절대 금지
- 마지막은 반드시 "~~분들께 큰 칭찬 부탁드립니다."로 마무리
제목 스타일: 감정 자극, 호기심 유발
예시: "사고 낸 엄마가 길 위에서 무릎 꿇고 오열한 이유"
"""
    else:
        style_guide = """
나레이션 스타일 (아래 톤을 반드시 따르세요):
- "~했는데...", "~하죠.", "~했다고 합니다." 로 자연스럽게 연결
- 시청자에게 직접 질문 절대 금지
- 짧고 간결하게, 약간의 유머와 여운 포함
- 마지막은 담백한 한 줄 교훈이나 여운으로 마무리
- 음슴체 절대 금지

나레이션 샘플:
"군대 체질이자 FM병사로 통했던 샤이니 키는 맞선임에게 군생활 최대의 반항을 했는데..."
"명령만 따르는 그 단순한 생활이 오히려 너무 행복했다고 하죠."
"군대에서 싸우면 원수 되기 쉽지만, 끝까지 버티면 전우가 되는 법이죠."

제목 스타일: 디시, 에펨코리아 스타일
예시: "22군번 월급 120만원 듣고 기절한 06해병 반응 실화임?"
"""

    prompt = f"""
이 영상을 분석해서 한국어 유튜브 쇼츠 대본을 만들어주세요.

[작업]
1. 영상 전체를 SRT 형식으로 전사 (타임라인 포함)
2. 쇼츠 주제 {shorts_count}개 발굴
3. 각 주제별 제목 {titles_per_topic}개 + 기승전결 대본

[카테고리: {category}]
{style_guide}

[자막 인용 형식 - 반드시 준수]
[00:00:11,000 --> 00:00:13,000] (화자명)
"대사 내용"

[JSON 형식으로만 출력]
{{
  "transcript": "SRT 형식 전체 전사본",
  "results": [
    {{
      "topic": "주제 한 줄 요약",
      "reason": "왜 시청자가 반응할지 1~2문장",
      "titles": ["제목1", "제목2", "제목3", "제목4", "제목5"],
      "script": "타임라인 포함한 기승전결 대본 전문"
    }}
  ]
}}
"""

    # 한글 파일명 문제 방지: 영문 임시 파일로 복사
    suffix = Path(audio_path).suffix
    safe_path = f"/tmp/snipply_upload{suffix}"
    shutil.copy2(audio_path, safe_path)

    mime_type, _ = mimetypes.guess_type(safe_path)
    if not mime_type:
        mime_type = "video/mp4"

    # 파일 업로드
    uploaded = client.files.upload(
        file=safe_path,
        config=types.UploadFileConfig(mime_type=mime_type)
    )

    # 처리 대기
    while uploaded.state.name == "PROCESSING":
        time.sleep(2)
        uploaded = client.files.get(name=uploaded.name)

    if uploaded.state.name == "FAILED":
        raise ValueError("Gemini 파일 업로드 실패")

    # 분석 요청
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Part.from_uri(file_uri=uploaded.uri, mime_type=mime_type),
            prompt
        ]
    )

    # 파일 삭제
    client.files.delete(name=uploaded.name)

    raw = response.text.strip()
    raw = re.sub(r"```json|```", "", raw).strip()

    data = json.loads(raw)
    return data.get("transcript", ""), data.get("results", [])
