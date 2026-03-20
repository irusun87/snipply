from google import genai
from google.genai import types
import os
import json
import re
import time


def generate_script_with_gemini(
    transcript: str,
    category: str = "감동",
    shorts_count: int = 3,
    titles_per_topic: int = 5
) -> list:
    """
    Whisper로 전사된 SRT 텍스트를 받아서
    Gemini 2.5 Pro (사고모드)로 대본을 생성합니다.
    """
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
당신은 한국 유튜브 쇼츠 전문 대본 작가입니다.
아래 SRT 전사본을 분석해서 쇼츠 주제와 대본을 작성해주세요.

[카테고리: {category}]
{style_guide}

[작업]
1. 쇼츠로 만들기 좋은 주제 {shorts_count}개 발굴
2. 각 주제별 제목 {titles_per_topic}개 + 기승전결 대본 작성

[자막 인용 형식 - 반드시 준수]
SRT 전사본의 타임라인을 그대로 가져와서 아래 형식으로 작성하세요.
절대로 타임라인을 생략하거나 임의로 만들지 마세요.

[00:00:11,000 --> 00:00:13,000] (화자명)
"대사 내용"

[JSON 형식으로만 출력 - 다른 텍스트 금지]
{{
  "results": [
    {{
      "topic": "주제 한 줄 요약",
      "reason": "왜 시청자가 반응할지 1~2문장",
      "titles": ["제목1", "제목2", "제목3", "제목4", "제목5"],
      "script": "타임라인 포함한 기승전결 대본 전문"
    }}
  ]
}}

[SRT 전사본]
{transcript}
"""

    # 2.5-pro 재시도 3회, 실패 시 2.5-flash로 폴백
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=8192)
                )
            )
            break
        except Exception as e:
            if "503" in str(e) and attempt < 2:
                time.sleep(10)
                continue
            # 3회 실패 시 flash로 폴백
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            break

    raw = response.text.strip()
    raw = re.sub(r"```json|```", "", raw).strip()

    data = json.loads(raw)
    return data.get("results", [])
