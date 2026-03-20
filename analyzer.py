import anthropic
import json
import re
import os


def analyze_and_generate(
    transcript: str,
    api_key: str = None,
    shorts_count: int = 3,
    titles_per_topic: int = 5
) -> list[dict]:
    client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""당신은 유튜브 쇼츠 전문 크리에이터입니다.
아래 전사본을 분석해서 JSON 형식으로만 응답해주세요.

[요청]
- 쇼츠 주제 {shorts_count}개 발굴
- 각 주제별 제목 {titles_per_topic}개 제안 (클릭을 유도하는 제목, SEO 최적화)
- 각 주제별 60초 쇼츠 대본 작성 (훅 → 본론 → CTA 구조, 약 150~180자)

[쇼츠 주제 선정 기준]
- 시청자가 "나도 이런 경험!" 하고 공감할 수 있는 순간
- 충격적이거나 반전이 있는 장면
- 실용적인 팁이나 정보가 담긴 부분
- 감정적으로 울림이 있는 순간

[JSON 출력 형식 - 반드시 이 형식만 출력]
{{
  "results": [
    {{
      "topic": "주제 한 줄 요약",
      "reason": "왜 시청자가 반응할지 1~2문장 설명",
      "titles": ["제목1", "제목2", "제목3", "제목4", "제목5"],
      "script": "훅으로 시작하는 60초 대본 전문"
    }}
  ]
}}

[전사본]
{transcript}"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    # JSON 파싱 (마크다운 코드블록 제거)
    raw = re.sub(r"```json|```", "", raw).strip()

    try:
        data = json.loads(raw)
        return data["results"]
    except json.JSONDecodeError:
        # 파싱 실패 시 원문 그대로 단일 항목으로 반환
        return [{
            "topic": "분석 결과",
            "reason": "JSON 파싱에 실패했습니다. 아래 원문을 확인해주세요.",
            "titles": ["제목을 불러오지 못했습니다."],
            "script": raw
        }]
