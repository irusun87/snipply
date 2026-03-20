from faster_whisper import WhisperModel
import streamlit as st


# 모델은 세션 전체에서 한 번만 로드 (재실행 시 재로드 방지)
@st.cache_resource(show_spinner=False)
def load_model(model_size: str = "large-v3"):
    """
    faster-whisper 모델 로드 (최초 1회, 이후 캐시)
    GPU 있으면 자동으로 CUDA 사용, 없으면 CPU(int8)로 폴백
    """
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        device = "cpu"

    compute_type = "float16" if device == "cuda" else "int8"
    return WhisperModel(model_size, device=device, compute_type=compute_type)


def transcribe_audio(audio_path: str, model_size: str = "large-v3", language: str = "ko") -> str:
    """
    로컬 faster-whisper로 오디오 전사.
    - GPU 없어도 동작 (CPU int8 모드)
    - GPU 있으면 float16으로 약 5~10배 빠름
    - 파일 크기 제한 없음 (API 대비 장점)
    """
    model = load_model(model_size)

    segments, _ = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        initial_prompt="유튜브 영상 전사입니다. 자연스러운 한국어로 전사해주세요."
    )

    return " ".join(seg.text.strip() for seg in segments).strip()
