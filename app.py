import streamlit as st
import os
from pathlib import Path

# Streamlit Cloud secrets → 환경변수 자동 주입
for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]:
    if key not in os.environ and hasattr(st, "secrets") and key in st.secrets:
        os.environ[key] = st.secrets[key]

from transcriber import transcribe_audio
from corrector import correct_transcript
from analyzer import analyze_and_generate
from gemini_transcriber import generate_script_with_gemini

st.set_page_config(page_title="Snipply", page_icon="🎬", layout="centered")

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
.category-감동 { border-left-color: #E05C97 !important; }
.category-군대 { border-left-color: #3D8B37 !important; }
</style>
""", unsafe_allow_html=True)

# API 키 확인
if not os.getenv("ANTHROPIC_API_KEY") or not os.getenv("OPENAI_API_KEY"):
    st.error("⚠️ API 키가 설정되지 않았습니다. 관리자에게 문의하세요.")
    st.stop()

st.title("🎬 Snipply")
st.caption("영상을 업로드하면 AI가 쇼츠 주제와 대본을 자동으로 만들어드립니다.")
st.divider()

# ── 사이드바 ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 생성 옵션")

    # 엔진 선택
    st.subheader("🔧 대본 생성 엔진")
    engine = st.radio(
        "엔진 선택",
        options=["Claude", "Gemini Pro"],
        horizontal=True,
        label_visibility="collapsed"
    )
    if engine == "Claude":
        st.caption("✅ 안정적 · 빠름 · Claude Sonnet")
    else:
        if not os.getenv("GEMINI_API_KEY"):
            st.warning("⚠️ GEMINI_API_KEY가 설정되지 않았습니다.")
        st.caption("🧠 사고모드 · 고품질 · Gemini 2.5 Pro")

    st.divider()

    # 카테고리 선택
    st.subheader("📂 콘텐츠 카테고리")
    category = st.radio(
        "카테고리 선택",
        options=["감동", "군대"],
        horizontal=True,
        label_visibility="collapsed"
    )
    if category == "감동":
        st.caption("💜 감동/사연 특화 · 존댓말 나레이션")
    else:
        st.caption("🟢 군대/커뮤니티 특화 · 디씨 감성")

    st.divider()

    shorts_count = st.slider("발굴할 쇼츠 주제 수", 1, 5, 3)
    titles_per_topic = st.slider("주제당 제목 제안 수", 3, 5, 5)

    st.divider()
    st.caption("🔒 API 키는 서버에서 관리됩니다.")

# ── 파일 업로드 ────────────────────────────────────────────────────────
st.subheader("1️⃣ 영상 업로드")
uploaded = st.file_uploader(
    "영상 또는 오디오 파일을 업로드하세요",
    type=["mp4", "mov", "mp3", "wav", "m4a"]
)

run_btn = st.button(
    f"▶ [{category}] 분석 시작  |  {engine}",
    type="primary",
    use_container_width=True,
    disabled=uploaded is None
)

# ── 파이프라인 실행 ────────────────────────────────────────────────────
if run_btn and uploaded:
    st.divider()
    try:
        # 파일 저장
        with st.status("📥 파일 준비 중...", expanded=True) as s:
            tmp_path = Path("/tmp") / uploaded.name
            tmp_path.write_bytes(uploaded.read())
            audio_path = str(tmp_path)
            s.update(label="✅ 파일 준비 완료", state="complete")

        # ── 공통: Whisper 전사 ─────────────────────────────────────────
        with st.status("🎙️ Whisper 전사 중...", expanded=True) as s:
            raw_transcript = transcribe_audio(audio_path)
            s.update(label="✅ 전사 완료", state="complete")

        with st.expander("📄 원본 전사 결과 보기"):
            st.text_area("", raw_transcript, height=150,
                         label_visibility="collapsed", key="raw_transcript")

        # ── 공통: Claude 교정 ──────────────────────────────────────────
        with st.status("✍️ 전사본 교정 중...", expanded=True) as s:
            corrected = correct_transcript(raw_transcript)
            s.update(label="✅ 교정 완료", state="complete")

        with st.expander("📝 교정된 전사본 보기"):
            st.text_area("", corrected, height=150,
                         label_visibility="collapsed", key="corrected_transcript")

        # ── 대본 생성: 엔진에 따라 분기 ───────────────────────────────
        if engine == "Gemini Pro":
            with st.status("🧠 Gemini 2.5 Pro 사고 중...", expanded=True) as s:
                results = generate_script_with_gemini(
                    corrected,
                    category=category,
                    shorts_count=shorts_count,
                    titles_per_topic=titles_per_topic
                )
                s.update(label="✅ 완료!", state="complete")
        else:
            with st.status(f"🚀 Claude가 대본 생성 중...", expanded=True) as s:
                results = analyze_and_generate(
                    corrected,
                    shorts_count=shorts_count,
                    titles_per_topic=titles_per_topic,
                    category=category
                )
                s.update(label="✅ 완료!", state="complete")

        # ── 결과 출력 ──────────────────────────────────────────────────
        st.divider()
        st.subheader(f"🎯 [{category}] 쇼츠 주제 & 대본")

        for i, item in enumerate(results, 1):
            st.markdown(f"<div class='result-card category-{category}'>", unsafe_allow_html=True)
            st.markdown(f"<span class='badge'>주제 {i}</span>", unsafe_allow_html=True)
            st.markdown(f"### {item['topic']}")
            st.markdown(f"**왜 반응할까?** {item['reason']}")

            st.markdown("**📌 추천 제목**")
            for j, title in enumerate(item["titles"], 1):
                st.markdown(f"{j}. {title}")

            st.markdown("**🎬 쇼츠 대본**")
            st.text_area("대본", value=item["script"], height=300,
                         label_visibility="collapsed",
                         key=f"script_{engine}_{category}_{i}")
            st.markdown("</div>", unsafe_allow_html=True)

        # 전체 다운로드
        st.divider()
        full_text = f"[카테고리: {category}] [엔진: {engine}]\n\n" + "\n\n".join([
            f"=== 주제 {i}: {r['topic']} ===\n[왜 반응할까]\n{r['reason']}\n\n"
            f"[추천 제목]\n" + "\n".join(f"{j+1}. {t}" for j, t in enumerate(r["titles"])) +
            f"\n\n[대본]\n{r['script']}"
            for i, r in enumerate(results, 1)
        ])
        st.download_button(
            "📥 전체 결과 다운로드 (.txt)",
            data=full_text,
            file_name=f"snipply_{category}_{engine}_results.txt",
            mime="text/plain",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
        st.info("파일 형식과 크기를 확인해주세요.")
