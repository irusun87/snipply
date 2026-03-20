# 🎬 유튜브 쇼츠 생성기 v2

YouTube 영상 링크를 넣으면 로컬 Whisper + Claude AI가
쇼츠 주제, 제목, 대본을 자동 생성합니다.

## 변경 사항 (v2)
- Whisper: OpenAI API → 로컬 faster-whisper (무료, 파일 크기 제한 없음)
- API 키: 팀원 입력 불필요 → 서버에서 관리

---

## 🚀 Streamlit Cloud 배포 (팀원 공유용)

### 1. GitHub에 올리기
```bash
git init
git add .
git commit -m "init"
git remote add origin https://github.com/YOUR_ID/youtube-shorts-gen.git
git push -u origin main
```

### 2. Streamlit Cloud 배포
1. https://share.streamlit.io 접속 (GitHub 로그인)
2. New app → 저장소 선택 → Main file: `app.py`
3. Deploy

### 3. API 키 등록
배포된 앱 → 우측 상단 ⋮ → Settings → Secrets:
```
ANTHROPIC_API_KEY = "sk-ant-실제키입력"
```

### 4. 팀원 공유
생성된 URL 공유 끝! 팀원은 브라우저에서 바로 사용

---

## 💻 로컬 실행

```bash
# 패키지 설치
pip install -r requirements.txt

# ffmpeg 필수 (오디오 변환)
# Mac:    brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: https://ffmpeg.org/download.html

# API 키 설정
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# secrets.toml 열어서 실제 키 입력

# 실행
streamlit run app.py
```

---

## ⚙️ Whisper 모델 선택 가이드

| 모델 | VRAM | CPU 속도(30분 영상) | 품질 |
|------|------|-------------------|------|
| large-v3 | 3GB | ~15분 | 최고 ⭐⭐⭐⭐⭐ |
| medium | 2GB | ~8분 | 우수 ⭐⭐⭐⭐ |
| small | 1GB | ~4분 | 양호 ⭐⭐⭐ |
| tiny | 0.5GB | ~2분 | 기본 ⭐⭐ |

GPU 없으면 medium 권장. 최초 실행 시 모델 자동 다운로드.

---

## 💰 비용
- Whisper: **무료** (로컬 실행)
- Claude API: 30분 영상 기준 약 $0.05 (≈ 70원)
- Streamlit Cloud: **무료** (소규모 팀)
