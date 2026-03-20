from openai import OpenAI
import os
import re


def transcribe_audio(audio_path: str, model_size: str = None, language: str = "ko") -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # 1단계: whisper-1로 SRT 타임라인 추출
    with open(audio_path, "rb") as f:
        srt_raw = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="ko",
            response_format="srt",
            prompt="한국어 유튜브 콘텐츠 전사입니다."
        )

    # 2단계: gpt-4o-transcribe로 텍스트 품질 교정
    # SRT에서 타임라인과 텍스트 분리
    blocks = re.split(r'\n\n+', srt_raw.strip())
    corrected_blocks = []

    texts = []
    metas = []  # 번호 + 타임라인 보존

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            metas.append('\n'.join(lines[:2]))  # 번호 + 타임라인
            texts.append(' '.join(lines[2:]))   # 텍스트만
        elif len(lines) == 2:
            metas.append(lines[0])
            texts.append(lines[1])

    # 텍스트 전체를 한 번에 교정 요청
    combined_text = '\n'.join(f"[{i+1}] {t}" for i, t in enumerate(texts))

    correction_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "한국어 유튜브 전사 텍스트 교정 전문가입니다. "
                    "번호 순서대로 각 텍스트의 오탈자, 잘못 인식된 단어만 교정하세요. "
                    "군대 용어(병장, 이병, 해병대, UDT, 특전사, 전역, 복무, 훈련소), "
                    "연예인 이름, 방송명을 정확하게 수정하세요. "
                    "내용과 순서는 절대 바꾸지 말고 [번호] 형식 그대로 출력하세요."
                )
            },
            {"role": "user", "content": combined_text}
        ]
    )

    corrected_text = correction_response.choices[0].message.content.strip()

    # 교정된 텍스트 파싱
    corrected_lines = {}
    for line in corrected_text.split('\n'):
        match = re.match(r'\[(\d+)\]\s+(.*)', line.strip())
        if match:
            corrected_lines[int(match.group(1))] = match.group(2)

    # 타임라인 + 교정 텍스트 재조합
    for i, meta in enumerate(metas):
        text = corrected_lines.get(i + 1, texts[i])
        corrected_blocks.append(f"{meta}\n{text}")

    return '\n\n'.join(corrected_blocks)
