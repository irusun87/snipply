import anthropic
import os


def correct_transcript(raw_text: str, api_key: str = None) -> str:
    """
    Claude API로 Whisper 전사본의 오탈자와 어색한 표현을 교정합니다.
    원문의 내용과 뉘앙스는 최대한 유지합니다.
    """
    client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    prompt = f"""다음은 음성 인식(Whisper)으로 생성된 전사 텍스트입니다.
아래 기준으로 교정해주세요:

1. 명백한 오탈자, 잘못 인식된 단어 수정 (예: "안녕하세여" → "안녕하세요")
2. 고유명사, 브랜드명, 전문 용어 교정
3. 문장 부호 추가 (마침표, 쉼표 등)
4. 발화 특성 제거 (어…, 음…, 그…, 저…)
5. 원문의 내용, 어조, 표현은 절대 바꾸지 말 것
6. 교정된 텍스트만 출력 (설명 없이)

[원본 전사]
{raw_text}"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text.strip()
