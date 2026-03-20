import anthropic
import os


def correct_transcript(raw_text: str, api_key: str = None) -> str:
    client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""다음은 SRT 형식의 전사 텍스트입니다.
SRT 형식(타임라인, 번호)은 반드시 그대로 유지하면서 아래 기준으로만 교정해주세요:

1. 명백한 오탈자, 잘못 인식된 단어 수정
2. 고유명사, 브랜드명, 전문 용어 교정
3. 발화 특성 제거 (어…, 음…, 그…, 저…)
4. 타임라인 번호 형식은 절대 변경 금지
5. 교정된 SRT 텍스트만 출력 (설명 없이)

[원본 SRT]
{raw_text}"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text.strip()
