import streamlit as st
import os
from pathlib import Path

# Streamlit Cloud secrets → 환경변수 자동 주입
for key in ["ANTHROPIC_API_KEY"]:
    if key not in os.environ and hasattr(st, "secrets") and key in st.secrets:
        os.environ[key] = st.secrets[key]

from downloader import download_audio
from transcriber import transcribe_audio
from corrector import correct_transcript
from analyzer import analyze_and_generate

st.set_page_config(page_title="유튜브 쇼츠 생성기", page_icon="🎬", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.result-card {
    background: #f8f9ff;
    border-left: 4px solid #5B5FEF;
    border-radius: 8px;
    padding: 20px 24px;
    margin: 16px 0;
}
.badge {
    background: #5B5FEF; color: white;
    padding: 3px 12px; border-radius: 20px;
    font-size: 12px; font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# API 키 유효성 확인 (서버에서만 로드)
claude_key = os.getenv("ANTHROPIC_API_KEY", "")
if not claude_key:
    st.error("⚠️ 서버에 ANTHROPIC_API_KEY가 설정되지 않았습니다. 관리자에게 문의하세요.")
    st.stop()

st.title("🎬 유튜브 쇼츠 생성기")
st.caption("영상 링크를 입력하면 AI가 쇼츠 주제와 대본을 자동으로 만들어드립니다.")
st.divider()

# 사이드바: 생성 옵션만 (API 키 입력창 없음)
with st.sidebar:
    st.header("⚙️ 생성 옵션")
    shorts_count = st.slider("발굴할 쇼츠 주제 수", 1, 5, 3)
    titles_per_topic = st.slider("주제당 제목 제안 수", 3, 5, 5)
    st.divider()
    st.subheader("🤖 Whisper 모델")
    model_size = st.selectbox(
        "모델 크기",
        options=["large-v3", "medium", "small", "base", "tiny"],
        index=0,
        help="large-v3: 최고품질(GPU권장) / medium: CPU도 가능 / small·tiny: 빠르지만 정확도↓"
    )
    st.caption("※ 최초 실행 시 모델 다운로드가 발생합니다.")
    st.divider()
    st.caption("🔒 API 키는 서버에서 관리됩니다.")

# 영상 입력
st.subheader("1️⃣ 영상 입력")
input_mode = st.radio("입력 방식", ["YouTube URL", "파일 업로드"], horizontal=True)

if input_mode == "YouTube URL":
    url = st.text_input("YouTube 링크", placeholder="https://www.youtube.com/watch?v=...")
    ready = bool(url)
else:
    uploaded = st.file_uploader("영상 또는 오디오 파일", type=["mp4", "mov", "mp3", "wav", "m4a"])
    ready = uploaded is not None

run_btn = st.button("▶ 분석 시작", type="primary", use_container_width=True, disabled=not ready)

if run_btn and ready:
    st.divider()
    try:
        with st.status("📥 오디오 추출 중...", expanded=True) as s:
            if input_mode == "YouTube URL":
                audio_path = download_audio(url)
            else:
                tmp_path = Path("/tmp") / uploaded.name
                tmp_path.write_bytes(uploaded.read())
                audio_path = str(tmp_path)
            s.update(label="✅ 오디오 추출 완료", state="complete")

        with st.status(f"🎙️ Whisper({model_size}) 전사 중...", expanded=True) as s:
            raw_transcript = transcribe_audio(audio_path, model_size=model_size)
            s.update(label="✅ 전사 완료", state="complete")

        with st.expander("📄 원본 전사 결과 보기"):
            st.text_area("", raw_transcript, height=150, label_visibility="collapsed")

        with st.status("✍️ Claude가 전사본 교정 중...", expanded=True) as s:
            corrected = correct_transcript(raw_transcript)
            s.update(label="✅ 교정 완료", state="complete")

        with st.expander("📝 교정된 전사본 보기"):
            st.text_area("", corrected, height=150, label_visibility="collapsed")

        with st.status("🚀 쇼츠 주제 및 대본 생성 중...", expanded=True) as s:
            results = analyze_and_generate(corrected, shorts_count=shorts_count, titles_per_topic=titles_per_topic)
            s.update(label="✅ 완료!", state="complete")

        st.divider()
        st.subheader("🎯 쇼츠 주제 & 대본")

        for i, item in enumerate(results, 1):
            st.markdown("<div class='result-card'>", unsafe_allow_html=True)
            st.markdown(f"<span class='badge'>주제 {i}</span>", unsafe_allow_html=True)
            st.markdown(f"### {item['topic']}")
            st.markdown(f"**왜 반응할까?** {item['reason']}")
            st.markdown("**📌 추천 제목**")
            for j, title in enumerate(item["titles"], 1):
                st.markdown(f"{j}. {title}")
            st.markdown("**🎬 쇼츠 대본**")
            st.text_area("대본", value=item["script"], height=220,
                         label_visibility="collapsed", key=f"script_{i}")
            st.markdown("</div>", unsafe_allow_html=True)

        full_text = "\n\n".join([
            f"=== 주제 {i}: {r['topic']} ===\n[왜 반응할까]\n{r['reason']}\n\n"
            f"[추천 제목]\n" + "\n".join(f"{j+1}. {t}" for j, t in enumerate(r["titles"])) +
            f"\n\n[대본]\n{r['script']}"
            for i, r in enumerate(results, 1)
        ])
        st.divider()
        st.download_button("📥 전체 결과 다운로드 (.txt)", data=full_text,
                           file_name="shorts_results.txt", mime="text/plain",
                           use_container_width=True)

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
        st.info("영상 URL 또는 파일을 다시 확인해주세요.")
