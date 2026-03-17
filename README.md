# 🎓 강사 페이지 빌더 Pro

AI 기반 수능 강사 랜딩페이지 생성기 (Streamlit + Gemini API)

## 🚀 배포 방법 (5분 완성)

### 1단계 — GitHub 업로드
1. [github.com](https://github.com) 로그인
2. `New repository` → 이름: `landing-page-builder`
3. `Add file` → `Upload files` → 이 폴더의 파일 2개 업로드
   - `app.py`
   - `requirements.txt`
4. `Commit changes` 클릭

### 2단계 — Streamlit Cloud 배포
1. [share.streamlit.io](https://share.streamlit.io) 접속
2. GitHub 계정으로 로그인
3. `New app` 클릭
4. Repository: `landing-page-builder` 선택
5. Main file path: `app.py`
6. `Deploy!` 클릭 → 2~3분 후 URL 발급

### 3단계 — Gemini API 키 발급 (무료)
1. [aistudio.google.com](https://aistudio.google.com) 접속
2. 구글 계정으로 로그인
3. `Get API Key` → `Create API Key`
4. 앱 사이드바의 `API Key` 칸에 붙여넣기

---

## ✨ 기능

| 기능 | 설명 |
|------|------|
| 🎨 **7가지 프리셋 테마** | 벚꽃·파이어·오션·럭셔리·에코·윈터·코스모스 |
| ✦ **AI 무한 컨셉 생성** | 자유 묘사로 나만의 테마 생성 |
| 🎲 **랜덤 AI 생성** | 15가지 무드 중 랜덤 선택 |
| ✍️ **AI 전체 문구 생성** | 배너·소개·이유·커리큘럼·CTA 등 |
| ✏️ **문구 직접 편집** | 생성된 문구 실시간 수정 |
| 📑 **섹션 선택** | 원하는 섹션만 ON/OFF |
| 📥 **HTML 다운로드** | 완성된 랜딩페이지 파일 저장 |

## 💡 사용 팁

- **Gemini 무료 API**: 분당 15회 제한 → 연속 클릭 피하기
- **AI 문구 생성**: 맥락을 구체적으로 입력할수록 품질이 높아집니다
- **컨셉 생성 후 HTML 다운로드**: 완성된 HTML을 Netlify에 바로 배포 가능

## 🔧 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📌 무료 API 한도

| API | 무료 한도 | 비고 |
|-----|---------|------|
| Gemini 2.0 Flash | 분당 15회, 일 1500회 | **권장** |
| Gemini 1.5 Flash | 분당 15회, 일 1500회 | 자동 폴백 |
| Gemini 1.5 Flash-8B | 분당 15회, 일 1500회 | 자동 폴백 |
