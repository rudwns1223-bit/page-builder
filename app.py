"""
강사 페이지 빌더 Pro v7 — RADICAL REDESIGN
- 15개 테마 (8 신규: cinematic, stadium, acid, floral, inception, violet_pop, brutal, amber)
- 6가지 히어로 레이아웃 (typographic, cinematic, billboard, split_bold, editorial_bold, split)
- 배경 이미지 개선 (한국어 무드 → 정밀 영어 키워드)
- 파격적 디자인 시스템 + 클립패스 섹션 구분선
"""
import streamlit as st
import requests
import json, re, time, random, unicodedata, base64

st.set_page_config(
    page_title="강사 페이지 빌더 Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════
_D = {
    "api_key": "", "concept": "acid", "custom_theme": None,
    "instructor_name": "", "subject": "영어",
    "purpose_label": "2026 수능 파이널 완성",
    "purpose_type": "신규 커리큘럼", "target": "고3·N수",
    "custom_copy": None, "bg_photo_url": "",
    "active_sections": ["banner","intro","why","curriculum","cta"],
    "ai_mood": "", "inst_profile": None, "last_seed": None,
    "custom_section_on": False, "custom_section_topic": "",
    "uploaded_bg_b64": "",
    "pixabay_key": "", "bg_cache": {}, "preview_key": 0,
    "copy_tone": "🔥 강렬·도발",
    "history": [],
}
for _k, _v in _D.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

if not st.session_state.api_key:
    try:
        st.session_state.api_key = st.secrets.get("GROQ_API_KEY", "")
        if not st.session_state.pixabay_key:
            st.session_state.pixabay_key = st.secrets.get("PIXABAY_API_KEY", "")
    except Exception:
        pass

# ══════════════════════════════════════════════════════
# 상수
# ══════════════════════════════════════════════════════
GROQ_URL    = "https://api.groq.com/openai/v1/chat/completions"
# 기존 COPY_TONES 딕셔너리를 아래로 교체 (83행)
COPY_TONES = {
    "🔥 강렬·도발": (
        "어조: 직접적·도전적. 수험생의 현실 안일함을 정면으로 찌름. "
        "'아직도 감으로 공부해?' '남은 시간이 없어요' 같은 긴장감 문체. "
        "문장은 짧고 끊어쳐야 함. 마침표 대신 줄바꿈. 감탄문·의문문 적극 활용."
    ),
    "🤝 친근·공감": (
        "어조: 선배 느낌. 학생의 고민을 먼저 말해주는 방식. "
        "'저도 그 막막함 알아요' '이 느낌 있죠?' 같은 공감 문체. "
        "따뜻하지만 구체적. 추상적 위로 금지 — 반드시 구체적 상황 묘사 포함."
    ),
    "💎 프리미엄·권위": (
        "어조: 절제된 고급 브랜드 톤. '선택받은 수험생만의 커리큘럼' 느낌. "
        "수식어 최소화, 사실과 결과 중심. 문장 끝을 명사형으로 마무리. "
        "과장 금지 — 단 하나의 가장 강한 근거만 제시."
    ),
    "😎 쿨·MZ": (
        "어조: 트렌디하고 간결. '솔직히 말할게요' '그냥 됩니다' 같은 직설 문체. "
        "긴 문장 금지. 한 줄에 하나의 메시지. 이모지 1~2개 허용. "
        "설명하지 말고 결과만 말할 것."
    ),
    "📖 차분·신뢰": (
        "어조: 전문적·데이터 중심. '기출 분석 결과' '패턴 기반 학습' 같은 근거 제시형. "
        "숫자 대신 '반복 패턴', '출제 원리'로 구체화. "
        "신뢰는 주장이 아니라 방법론으로 쌓아야 함."
    ),
}

GROQ_MODELS = [
    "llama-3.3-70b-versatile",          # 메인 (기존 유지)
    "meta-llama/llama-4-scout-17b-16e-instruct",  # Llama 4 Scout
    "qwen/qwen3-32b",                   # Qwen 3 32B
    "llama-3.1-8b-instant",             # 경량 빠른 모델 (gemma2-9b-it 후계)
]

# ── 문구 스타일 예시 (Few-shot) ──────────────────────
FEW_SHOT_EXAMPLES = """
=== 레퍼런스 스타일 핵심 규칙 ===
- bannerTitle은 반드시 강사의 고유 커리큘럼 브랜드명 사용 (LIM IT, SYNTAX, R'GORITHM, CIRCLE 같은 방식)
  예) 커리큘럼명이 "KISS Logic"이면 bannerTitle = "KISS Logic"
  예) 커리큘럼명이 "인셉션"이면 bannerTitle = "인셉션"
- bannerSub은 과목+포지션 (예: "영어 독해의 절대 기준", "사회탐구 성공의 전제")
- brandTagline은 반드시 영어 한 문장 포함 (예: "Conquer the Pattern. Master the Score.")
- introDesc 도입부는 반드시 학생 고민에서 시작 ("아직도 지문이 안 읽히나요?" 방식)

[bannerTitle — 브랜드명 전면 배치 스타일]
- KISS Logic
- 인셉션
- R'GORITHM
- All Of KICE

[bannerSub — 포지셔닝 문구]
- 영어 독해의 절대 기준
- 수학 1등급의 유일한 루트
- 국어 비문학, 이제 다르게 읽힌다

[brandTagline — 영어 슬로건 필수 포함]
- "The Beginning Is Always Here."
- "Conquer the Pattern. Master the Score."
- "Read Different. Score Different."
- "One Method. One Direction. One Grade."

[introDesc — 학생 고민 먼저 시작]
- 지문은 읽히는데 답이 안 보이는 학생들이 있습니다. 어법은 외웠는데 실전에서 틀리는 학생들이 있습니다. 이 강의는 그 지점을 정확히 짚습니다.
- 공부는 하는데 성적이 안 오르는 느낌, 다들 한번씩 겪습니다. 문제는 방법이 아니라 방향입니다.
=== 절대 규칙 (위반 시 전체 실패) ===
- 강사 정보에 명시된 과목만 언급. 영어 강사면 영어만, 수학 강사면 수학만.
- 학교명·직위·소속·경력은 강사 정보에 없으면 절대 지어내지 말 것.
- "교수" 직함 절대 금지 — 반드시 "선생님" 또는 "강사".
- 확인되지 않은 수치(합격생 수, 만족도 %) 절대 금지.

=== 실제 사용된 좋은 문구 예시 (스타일 참고용 — 그대로 쓰지 말고 더 창의적으로) ===

[bannerTitle 스타일]
- [커리큘럼명], 우리의 역사적 순간이 시작됩니다.
- 1등급의 공식, [커리큘럼명]으로 완성하다
- 결정적인 순간, [커리큘럼명]이 답입니다
- 꼭 필요한 것만 담았다. [커리큘럼명]

[bannerLead 스타일 — 60-90자, 구체적·감정적]
- 당신에게 필요한 것만 골라 담았습니다. 출제 원리부터 실전 적용까지, 1등급을 위한 커리큘럼을 경험하세요.
- 시험장에서 흔들리지 않으려면 지금 이 커리큘럼이 필요합니다. 전략적 학습 설계로 성적 상승을 직접 체감하세요.
- 성적이 오르는 공부에는 이유가 있습니다. 강사가 직접 설계한 합격 커리큘럼으로 그 차이를 확인하세요.

[brandTagline 스타일 — 군더더기 없는 한 문장]
- 개념도, 풀이도, 실전도 — 이 강의 하나면 충분합니다.
- 더 이상 강의 쇼핑은 그만. 필요한 건 딱 이 커리큘럼입니다.
- 처음부터 끝까지, 완성형 커리큘럼.

[introTitle 스타일]
- 이 강의, 왜 이 선생님이어야 할까요?
- 수험생을 가장 잘 아는 선생님
- 결과로 말하는 선생님

[introDesc 스타일 — 80-120자, 신뢰감·구체성]
- 수년간 수험생과 함께 합격의 루트를 다듬어온 강사입니다. 기출 분석과 실전 풀이에 최적화된 수업으로 성적 상승을 직접 이끌어 왔습니다.
- 출제 원리를 꿰뚫는 분석력과 수험생 눈높이에 맞는 설명으로 매해 우수한 합격 실적을 만들어온 강사입니다.
- 강의 설계부터 문제 선별, 피드백까지 수험생의 점수 상승만을 위해 모든 과정을 직접 기획합니다.

[introBio 스타일 — 60자, 압축적]
- 매해 수험생과 압도적 결과를 만들어온 강사
- 탄탄한 개념과 실전 풀이를 모두 잡는 통합형 커리큘럼 설계자

[whyTitle 스타일]
- 지금, 이 강의여야 하는 3가지 이유
- 성적이 오르는 데는 이유가 있습니다

[whyReasons 스타일 — 제목은 짧고 임팩트, 설명은 구체적]
- 출제 경향을 꿰뚫는 분석력 | 기출 문제의 반복 패턴과 출제 원리를 체계적으로 분석하여 실전에서 바로 적용할 수 있도록 설계합니다.
- 군더더기 없는 핵심 콘텐츠 | 불필요한 내용을 걷어내고 점수에 직결되는 핵심만 담아 학습 효율을 극대화합니다.
- 1등급으로 가는 최단 루트 | 불필요한 학습을 줄이고 성적 향상에 직결되는 핵심 루트만 빠르게 공략합니다.

[curriculumTitle 스타일]
- 이렇게 공부합니다
- 합격까지 이어지는 학습 단계

[curriculumSteps 스타일 — 단계명은 행동어, 설명은 왜/어떻게]
- 기초 개념 완성 | 핵심 개념을 정확하게 이해하고 내 것으로 만드는 단계
- 기출 유형 분석 | 역대 기출 문제의 패턴을 파악하고 풀이 전략을 습득하는 단계
- 실전 적용 훈련 | 실제 시험과 동일한 조건으로 풀이 감각을 끌어올리는 단계

[targetTitle 스타일]
- 이런 수험생에게 딱 맞습니다
- 당신에게 필요한 강의입니다

[targetItems 스타일 — 40자 이상, 학생 상황 구체 묘사]
- 현재 성적에서 한 단계 더 도약하고 싶은 수험생
- 개념은 알겠는데 문제 풀이에서 자꾸 막히는 학생
- 체계적인 학습 루트 없이 혼자 공부하다 지친 수험생
- 감에 의존한 공부에서 벗어나 전략적으로 준비하고 싶은 수험생

[ctaTitle 스타일]
- 오늘이 가장 빠른 시작입니다
- 합격을 향한 첫 걸음, 지금 시작하세요

[ctaSub 스타일]
- 합격한 선배들의 선택, 이제 여러분의 차례입니다.
- 선착순 혜택이 마감되기 전, 지금 신청하세요.

[이벤트 bannerTitle 스타일]
- 이번 이벤트, 놓치면 다음 기회는 없습니다
- 앞으로 함께할 여러분을 위해 특별한 선물을 드립니다

[이벤트 deadlineMsg 스타일 — 긴박감]
- 선착순 마감 이벤트입니다. 정원이 가득 차면 신청이 종료되니 지금 바로 확인하세요.
- 기간이 지나면 참여가 불가합니다. 지금 바로 조건을 확인하고 혜택을 챙겨가세요.

[기획전 festHeroTitle 스타일]
- 수능 [과목]의 새로운 기준
- 한 번에 다 잡는 기획전이 열립니다

[기획전 festCtaSub 스타일]
- 선착순으로 마감되는 기획전입니다. 서두르세요.
- 이 혜택은 이번 기획전에서만 제공됩니다.
"""

# ── 15개 테마 ──────────────────────────────────────
THEMES = {
    # ━━ 기존 테마 (개선됨) ━━━━━━━━━━━━━━━━━
    "sakura": {
        "label":"🌸 벚꽃 봄","dark":False,
        "fonts":"https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;700&display=swap",
        "vars":"--c1:#B5304A;--c2:#E89BB5;--c3:#F5CEDA;--c4:#2A111A;--bg:#FBF6F4;--bg2:#F7EFF1;--bg3:#F2E5E9;--text:#2A111A;--t70:rgba(42,17,26,.7);--t45:rgba(42,17,26,.45);--bd:rgba(42,17,26,.10);--fh:'Playfair Display','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:12px;--r-btn:100px;",
        "extra_css":".hero-deco{font-style:italic}",
        "cta":"linear-gradient(135deg,#2A111A,#B5304A)","heroStyle":"editorial_bold"},
    "fire": {
        "label":"🔥 다크 파이어","dark":True,
        "fonts":"https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@400;700;900&family=DM+Sans:wght@300;400;700&display=swap",
        "vars":"--c1:#FF4500;--c2:#FF8C00;--c3:#FFD700;--c4:#0D0705;--bg:#0D0705;--bg2:#130A04;--bg3:#1A0E06;--text:#F1F5F9;--t70:rgba(241,245,249,.7);--t45:rgba(241,245,249,.45);--bd:rgba(255,69,0,.22);--fh:'Bebas Neue','Noto Sans KR',sans-serif;--fb:'DM Sans','Noto Sans KR',sans-serif;--r:4px;--r-btn:4px;",
        "extra_css":"",
        "cta":"linear-gradient(135deg,#0D0705,#FF4500 60%,#FF8C00)","heroStyle":"typographic"},
    "ocean": {
        "label":"🌊 오션 블루","dark":False,
        "fonts":"https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap",
        "vars":"--c1:#0EA5E9;--c2:#38BDF8;--c3:#BAE6FD;--c4:#0C4A6E;--bg:#F0F9FF;--bg2:#E0F2FE;--bg3:#BAE6FD;--text:#0C1A2E;--t70:rgba(12,26,46,.7);--t45:rgba(12,26,46,.45);--bd:rgba(14,165,233,.15);--fh:'Syne','Noto Sans KR',sans-serif;--fb:'Noto Sans KR',sans-serif;--r:10px;--r-btn:100px;",
        "extra_css":"",
        "cta":"linear-gradient(135deg,#0C4A6E,#0EA5E9)","heroStyle":"split"},
    "luxury": {
        "label":"✨ 골드 럭셔리","dark":True,
        "fonts":"https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,500;0,600;1,300;1,500&family=Noto+Serif+KR:wght@300;400;600&family=DM+Sans:wght@300;400;500&display=swap",
        "vars":"--c1:#C8975A;--c2:#D4AF72;--c3:#EDD8A4;--c4:#0C0B09;--bg:#0C0B09;--bg2:#131108;--bg3:#1A1810;--text:#F5F0E8;--t70:rgba(245,240,232,.7);--t45:rgba(245,240,232,.45);--bd:rgba(200,151,90,.15);--fh:'Cormorant Garamond','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:2px;--r-btn:2px;",
        "extra_css":".st{font-weight:300;font-style:italic}",
        "cta":"linear-gradient(135deg,#0C0B09,#2A2010)","heroStyle":"editorial_bold"},
    "cosmos": {
        "label":"🌌 코스모스","dark":True,
        "fonts":"https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Noto+Sans+KR:wght@300;400;700&family=DM+Sans:wght@300;400;500&display=swap",
        "vars":"--c1:#7C3AED;--c2:#06B6D4;--c3:#A78BFA;--c4:#030712;--bg:#030712;--bg2:#080C18;--bg3:#0D1220;--text:#F1F5F9;--t70:rgba(241,245,249,.7);--t45:rgba(241,245,249,.45);--bd:rgba(124,58,237,.22);--fh:'Orbitron','Noto Sans KR',sans-serif;--fb:'DM Sans','Noto Sans KR',sans-serif;--r:0px;--r-btn:0px;",
        "extra_css":".st{letter-spacing:.1em;text-transform:uppercase}",
        "cta":"linear-gradient(135deg,#030712,#2D1B69)","heroStyle":"typographic"},
    "winter": {
        "label":"❄️ 윈터 스노우","dark":False,
        "fonts":"https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,600;0,700;0,800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap",
        "vars":"--c1:#1E40AF;--c2:#3B82F6;--c3:#BFDBFE;--c4:#0F172A;--bg:#F8FAFF;--bg2:#EFF6FF;--bg3:#DBEAFE;--text:#0F172A;--t70:rgba(15,23,42,.7);--t45:rgba(15,23,42,.45);--bd:rgba(30,64,175,.12);--fh:'Plus Jakarta Sans','Noto Sans KR',sans-serif;--fb:'Plus Jakarta Sans','Noto Sans KR',sans-serif;--r:8px;--r-btn:100px;",
        "extra_css":".st{font-weight:800}",
        "cta":"linear-gradient(135deg,#1E3A8A,#3B82F6)","heroStyle":"split"},
    "eco": {
        "label":"🌿 에코 그린","dark":False,
        "fonts":"https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;500;700&display=swap",
        "vars":"--c1:#059669;--c2:#34D399;--c3:#A7F3D0;--c4:#064E3B;--bg:#F0FDF4;--bg2:#DCFCE7;--bg3:#BBF7D0;--text:#064E3B;--t70:rgba(6,78,59,.7);--t45:rgba(6,78,59,.45);--bd:rgba(5,150,105,.15);--fh:'DM Serif Display','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:14px;--r-btn:100px;",
        "extra_css":"",
        "cta":"linear-gradient(135deg,#064E3B,#059669)","heroStyle":"split"},

    # ━━ 신규 파격 테마 ━━━━━━━━━━━━━━━━━━━━━━
    "cinematic": {
        "label":"🎬 시네마틱","dark":True,
        "fonts":"https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;500&display=swap",
        "vars":"--c1:#FF1744;--c2:#FF5252;--c3:#4A0010;--c4:#050005;--bg:#050005;--bg2:#0A000A;--bg3:#150010;--text:#F8F0F0;--t70:rgba(248,240,240,.7);--t45:rgba(248,240,240,.45);--bd:rgba(255,23,68,.2);--fh:'Bebas Neue','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:0px;--r-btn:2px;",
        "extra_css":".st{letter-spacing:.08em} section.alt{background:var(--bg2)} .clip-diag{clip-path:polygon(0 0,100% 5%,100% 100%,0 95%)}",
        "cta":"linear-gradient(135deg,#1A0005,#FF1744 55%,#FF5252)","heroStyle":"cinematic",
        "particle":"embers"},
    "stadium": {
        "label":"🏟️ 스타디움","dark":True,
        "fonts":"https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Noto+Sans+KR:wght@400;700;900&family=DM+Sans:wght@300;400;500&display=swap",
        "vars":"--c1:#FF2244;--c2:#FF6688;--c3:#3A0010;--c4:#020008;--bg:#020008;--bg2:#06000E;--bg3:#0C0018;--text:#F5F5FF;--t70:rgba(245,245,255,.7);--t45:rgba(245,245,255,.45);--bd:rgba(255,34,68,.22);--fh:'Black Han Sans','Noto Sans KR',sans-serif;--fb:'DM Sans','Noto Sans KR',sans-serif;--r:2px;--r-btn:2px;",
        "extra_css":".st{letter-spacing:.04em} .hero-num{font-family:'Black Han Sans',sans-serif;font-size:28vw;position:absolute;opacity:.04;color:var(--c1);line-height:1;top:-0.1em;right:-0.1em;pointer-events:none}",
        "cta":"linear-gradient(135deg,#020008,#FF2244 60%,#FF6688)","heroStyle":"typographic",
        "particle":"none"},
    "acid": {
        "label":"⚡ 에시드 그린","dark":True,
        "fonts":"https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Noto+Sans+KR:wght@400;700;900&display=swap",
        "vars":"--c1:#AAFF00;--c2:#CCFF44;--c3:#224400;--c4:#030703;--bg:#030703;--bg2:#060E06;--bg3:#0A1A0A;--text:#F0FFF0;--t70:rgba(240,255,240,.7);--t45:rgba(240,255,240,.45);--bd:rgba(170,255,0,.18);--on-c1:#030703;--fh:'Space Grotesk','Noto Sans KR',sans-serif;--fb:'Space Grotesk','Noto Sans KR',sans-serif;--r:0px;--r-btn:0px;",
        "extra_css":".st{letter-spacing:.02em} .card{border-color:rgba(170,255,0,.15)!important} .btn-p{color:#030703!important}",
        "cta":"linear-gradient(135deg,#7CFC00,#AAFF00)", 
        "heroStyle":"typographic",
        "particle":"none"},
    "floral": {
        "label":"🌸 플로럴 에디토리얼","dark":False,
        "fonts":"https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,600;0,700;1,300;1,600&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;500&display=swap",
        "vars":"--c1:#E8386D;--c2:#F472A8;--c3:#FFD6E7;--c4:#1A0510;--bg:#FFFAF8;--bg2:#FFF0F4;--bg3:#FFE4EE;--text:#1A0510;--t70:rgba(26,5,16,.7);--t45:rgba(26,5,16,.45);--bd:rgba(232,56,109,.12);--fh:'Cormorant Garamond','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:0px;--r-btn:100px;",
        "extra_css":".st{font-style:italic;font-weight:700} h1.st{font-size:clamp(48px,7vw,96px)!important}",
        "cta":"linear-gradient(135deg,#1A0510,#E8386D)","heroStyle":"editorial_bold",
        "particle":"petals"},
    "inception": {
        "label":"🌲 인셉션 에메랄드","dark":True,
        "fonts":"https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,600;1,300;1,600&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;500&display=swap",
        "vars":"--c1:#2DB87C;--c2:#4ECFA0;--c3:#0A3020;--c4:#010C06;--bg:#010C06;--bg2:#031408;--bg3:#061C0C;--text:#E8F5F0;--t70:rgba(232,245,240,.7);--t45:rgba(232,245,240,.45);--bd:rgba(45,184,124,.18);--fh:'Cormorant Garamond','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:4px;--r-btn:4px;",
        "extra_css":".st{font-style:italic} .accent-gold{color:#C8975A!important}",
        "cta":"linear-gradient(135deg,#010C06,#0A3020 50%,#2DB87C)","heroStyle":"editorial_bold",
        "particle":"leaves"},
    "violet_pop": {
        "label":"💜 바이올렛 팝","dark":False,
        "fonts":"https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,600;0,700;0,800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap",
        "vars":"--c1:#7C3AED;--c2:#9F67FF;--c3:#EDE9FF;--c4:#1E0A3C;--bg:#FAFAFF;--bg2:#F5F3FF;--bg3:#EDE9FF;--text:#1E0A3C;--t70:rgba(30,10,60,.7);--t45:rgba(30,10,60,.45);--bd:rgba(124,58,237,.12);--fh:'Plus Jakarta Sans','Noto Sans KR',sans-serif;--fb:'Plus Jakarta Sans','Noto Sans KR',sans-serif;--r:16px;--r-btn:100px;",
        "extra_css":".st{font-weight:800} .card{box-shadow:0 2px 20px rgba(124,58,237,.07)!important}",
        "cta":"linear-gradient(135deg,#4C1D95,#7C3AED)","heroStyle":"split_bold",
        "particle":"none"},
    "brutal": {
        "label":"◼️ 브루탈 모노","dark":False,
        "fonts":"https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Noto+Sans+KR:wght@400;700;900&display=swap",
        "vars":"--c1:#1A1A1A;--c2:#444444;--c3:#E0E0E0;--c4:#000000;--bg:#F5F5F0;--bg2:#EBEBEB;--bg3:#E0E0E0;--text:#0A0A0A;--t70:rgba(10,10,10,.7);--t45:rgba(10,10,10,.45);--bd:rgba(10,10,10,.15);--fh:'Space Grotesk','Noto Sans KR',sans-serif;--fb:'Space Grotesk','Noto Sans KR',sans-serif;--r:0px;--r-btn:0px;",
        "extra_css":".card{border:2px solid #0A0A0A!important;box-shadow:4px 4px 0 #0A0A0A!important} .btn-p{border:2px solid #fff!important;box-shadow:3px 3px 0 #fff!important} section.alt{background:var(--bg2)}",
        "cta":"linear-gradient(135deg,#0A0A0A,#333333)","heroStyle":"billboard",
        "particle":"none"},
    "amber": {
        "label":"🟠 앰버 글로우","dark":True,
        "fonts":"https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;500&display=swap",
        "vars":"--c1:#F59E0B;--c2:#FCD34D;--c3:#7A4A00;--c4:#080400;--bg:#080400;--bg2:#0E0800;--bg3:#160D00;--text:#FFF8E8;--t70:rgba(255,248,232,.7);--t45:rgba(255,248,232,.45);--bd:rgba(245,158,11,.18);--on-c1:#0A0A0A;--fh:'Playfair Display','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:4px;--r-btn:4px;",
        "extra_css":".st{font-style:italic}",
        "cta":"linear-gradient(135deg,#080400,#7A4A00 50%,#F59E0B)","heroStyle":"immersive",
        "particle":"gold"},
}

PURPOSE_SECTIONS = {
    "신규 커리큘럼": ["banner","intro","video","grade_stats","before_after","method","why","curriculum","target","package","reviews","faq","cta"],
    "이벤트":       ["banner","event_overview","event_benefits","event_deadline","reviews","cta"],
    "기획전":       ["fest_hero","fest_lineup","fest_benefits","fest_cta"],
}
PURPOSE_HINTS = {
    "신규 커리큘럼": "📚 강사 전문성·신뢰감 강조 — 인셉션, 앰버, 코스모스 추천",
    "이벤트":       "🎉 기간 한정·긴박감·혜택 강조 — 시네마틱, 에시드, 스타디움 추천",
    "기획전":       "🏆 강사 라인업·통합 혜택 강조 — 브루탈, 골드 럭셔리, 코스모스 추천",
}
PURPOSE_THEME_HINTS = {
    "이벤트":       "목적이 이벤트(기간한정·긴박감)입니다. cinematic·acid·stadium 같은 강렬한 어두운 테마를 선택하세요. 밝거나 자연적인 테마 금지.",
    "기획전":       "목적이 기획전(통합 라인업·프리미엄)입니다. brutal·luxury·cosmos 같이 임팩트 있는 테마를 선택하세요.",
    "신규 커리큘럼":"목적이 신규 커리큘럼(강사 신뢰·전문성)입니다. inception·amber·cosmos 같이 무게감 있는 테마를 선택하세요.",
}
SEC_LABELS = {
    "banner":"🏠 메인 배너","intro":"👤 강사 소개","why":"💡 필요한 이유",
    "curriculum":"📚 커리큘럼","target":"🎯 수강 대상","reviews":"⭐ 수강평",
    "faq":"❓ FAQ","cta":"📣 수강신청",
    "video":"🎬 영상 미리보기","before_after":"🔄 수강 전/후","method":"🧪 학습법 시각화","package":"📦 구성 안내",
    "grade_stats":"📊 등급 변화 성과",
    "event_overview":"📅 이벤트 개요","event_benefits":"🎁 이벤트 혜택",
    "event_deadline":"⏰ 마감 안내",
    "fest_hero":"🏆 기획전 히어로","fest_lineup":"👥 강사 라인업",
    "fest_benefits":"🎁 기획전 혜택","fest_cta":"📣 기획전 CTA",
    "custom_section":"✏️ 기타 섹션",
}
RANDOM_SEEDS = [
    # ── 스포츠 ──────────────────────────────────────
    {"mood":"관중이 가득찬 야구장 밤 전광판 붉은빛 함성","layout":"brutal","font":"display","particle":"none"},
    {"mood":"축구 경기장 잔디 조명 초록 밤 전광판 함성","layout":"brutal","font":"display","particle":"none"},
    {"mood":"농구 코트 나무 바닥 스포트라이트 NBA 에너지","layout":"brutal","font":"display","particle":"none"},
    {"mood":"복싱 링 위 스포트라이트 땀 격투 집중","layout":"brutal","font":"display","particle":"none"},
    {"mood":"수영장 물결 파란 레인 선수 출발대 새벽","layout":"immersive","font":"display","particle":"none"},
    # ── 자연·계절 ────────────────────────────────────
    {"mood":"극지방 오로라 청록 보라 새벽하늘 빙하","layout":"immersive","font":"display","particle":"stars"},
    {"mood":"겨울 새벽 눈 덮인 사찰 고요 집중 먹빛 설경","layout":"minimal","font":"serif","particle":"snow"},
    {"mood":"가을 단풍 교정 은행나무 따뜻한 주황 갈색 노을","layout":"organic","font":"serif","particle":"leaves"},
    {"mood":"봄 벚꽃 흩날리는 밤 조명 핑크 로맨틱","layout":"editorial","font":"serif","particle":"petals"},
    {"mood":"여름 밤 루프탑 인디고 블루 도시 스카이라인","layout":"immersive","font":"display","particle":"none"},
    {"mood":"태풍 전날 먹구름 번개 폭풍 드라마틱","layout":"immersive","font":"display","particle":"none"},
    {"mood":"사막 모래폭풍 황금빛 석양 드넓음","layout":"editorial","font":"serif","particle":"gold"},
    {"mood":"열대우림 정글 짙은 녹색 습기 비","layout":"organic","font":"serif","particle":"leaves"},
    {"mood":"화산 분화 용암 붉은 검정 극적","layout":"brutal","font":"display","particle":"embers"},
    # ── 도시·건축 ────────────────────────────────────
    {"mood":"사이버펑크 보라 네온사인 비오는 다크 도시","layout":"brutal","font":"display","particle":"none"},
    {"mood":"홍콩 야경 빽빽한 고층 네온 복잡 에너지","layout":"brutal","font":"display","particle":"none"},
    {"mood":"도쿄 시부야 교차로 군중 빗속 네온","layout":"brutal","font":"display","particle":"none"},
    {"mood":"뉴욕 타임스퀘어 광고판 눈부신 야경","layout":"billboard","font":"display","particle":"none"},
    {"mood":"파리 에펠탑 황금빛 밤 로맨틱 클래식","layout":"editorial","font":"serif","particle":"gold"},
    {"mood":"두바이 황금 마천루 사막 미래 럭셔리","layout":"editorial","font":"serif","particle":"gold"},
    {"mood":"런던 빅벤 안개 빗속 클래식 영국","layout":"editorial","font":"serif","particle":"none"},
    {"mood":"베를린 브루탈리즘 콘크리트 그레이 강렬","layout":"brutal","font":"sans","particle":"none"},
    {"mood":"서울 한강 야경 다리 빛 반사 도시","layout":"immersive","font":"display","particle":"none"},
    {"mood":"고딕 성당 스테인드글라스 빛 신비","layout":"editorial","font":"serif","particle":"none"},
    # ── 학습·수험 ────────────────────────────────────
    {"mood":"수험생 새벽 4시 형광등 책상 집중과 고요 먹빛","layout":"minimal","font":"mono","particle":"none"},
    {"mood":"빈 강의실 새벽 의자 칠판 분필가루 고요","layout":"minimal","font":"serif","particle":"none"},
    {"mood":"도서관 서가 오래된 책 세피아 먼지 빛","layout":"editorial","font":"serif","particle":"none"},
    {"mood":"노트 필기 형광펜 빽빽한 메모 집중 클로즈업","layout":"minimal","font":"mono","particle":"none"},
    {"mood":"시험지 위 연필 손 시계 긴장 순간","layout":"minimal","font":"mono","particle":"none"},
    # ── 우주·SF ──────────────────────────────────────
    {"mood":"우주 정거장 내부 홀로그램 코발트 블루 테크","layout":"immersive","font":"mono","particle":"stars"},
    {"mood":"블랙홀 이벤트 호라이즌 빛 왜곡 심우주","layout":"immersive","font":"mono","particle":"stars"},
    {"mood":"화성 표면 붉은 사막 탐사 미래","layout":"editorial","font":"mono","particle":"none"},
    {"mood":"AI 회로 기판 초록 데이터 흐름 매트릭스","layout":"brutal","font":"mono","particle":"none"},
    {"mood":"양자 컴퓨터 파란 빛 구체 에너지 추상","layout":"immersive","font":"mono","particle":"stars"},
    # ── 예술·문화 ────────────────────────────────────
    {"mood":"고대 이집트 황금 신전 사막 모래 오벨리스크","layout":"editorial","font":"serif","particle":"gold"},
    {"mood":"빈티지 옥스퍼드 도서관 가죽 책 양피지 세피아","layout":"editorial","font":"serif","particle":"none"},
    {"mood":"19세기 파리 아방가르드 예술 포스터 타이포","layout":"brutal","font":"display","particle":"none"},
    {"mood":"재즈 바 스모키 앰버 조명 클래식 무드","layout":"editorial","font":"serif","particle":"gold"},
    {"mood":"록 콘서트 무대 스포트라이트 연기 에너지","layout":"brutal","font":"display","particle":"embers"},
    {"mood":"발레 무용수 무대 스포트라이트 우아 흰색","layout":"editorial","font":"serif","particle":"none"},
    {"mood":"일본 전통 정원 벚꽃 고요 선 미학","layout":"minimal","font":"serif","particle":"petals"},
    {"mood":"바이킹 fjord 북유럽 회색 석조 웅장","layout":"editorial","font":"display","particle":"snow"},
    # ── 색감·무드 실험 ───────────────────────────────
    {"mood":"ABPS 스타일 순수 블랙 네온 그린 테크 UI","layout":"brutal","font":"sans","particle":"none"},
    {"mood":"에시드 형광 노랑 블랙 반전 그런지","layout":"brutal","font":"sans","particle":"none"},
    {"mood":"마젠타 핫핑크 플로럴 에디토리얼 여성적","layout":"magazine","font":"serif","particle":"petals"},
    {"mood":"네온 팝아트 비비드 원색 90s 리트로 레이브","layout":"brutal","font":"display","particle":"none"},
    {"mood":"순수 흑백 영화 필름 노이즈 모노크롬","layout":"brutal","font":"mono","particle":"none"},
    {"mood":"인디고 딥블루 오션 심해 어둠 고요","layout":"immersive","font":"serif","particle":"none"},
    {"mood":"앰버 황금빛 위스키 바 재즈 다크 럭셔리","layout":"editorial","font":"serif","particle":"gold"},
    {"mood":"바이올렛 퍼플 팝 컬러 현대적 밝은 에너지","layout":"modern","font":"sans","particle":"none"},
    {"mood":"다크 아카데미아 빅토리안 고딕 도서관 촛불","layout":"editorial","font":"serif","particle":"none"},
    {"mood":"인셉션 다크 에메랄드 고급 교육 프리미엄","layout":"editorial","font":"serif","particle":"leaves"},
    {"mood":"브루탈리즘 콘크리트 모노크롬 강렬 타이포","layout":"brutal","font":"sans","particle":"none"},
    {"mood":"미니멀 흰 공간 단 하나의 선 여백 호흡","layout":"minimal","font":"serif","particle":"none"},
    {"mood":"미래 우주선 내부 홀로그램 코발트 블루","layout":"immersive","font":"mono","particle":"stars"},
    {"mood":"스팀펑크 황동 기어 갈색 증기 빅토리안","layout":"editorial","font":"serif","particle":"gold"},
    {"mood":"글리치 아트 픽셀 깨짐 디지털 노이즈 에러","layout":"brutal","font":"mono","particle":"none"},
    {"mood":"수묵화 번지는 먹 여백 동양 미니멀","layout":"minimal","font":"serif","particle":"none"},
    {"mood":"홀로그램 무지개 빛 투명 미래 프리즘","layout":"immersive","font":"display","particle":"stars"},
    {"mood":"캠프파이어 불꽃 밤 숲 따뜻 원초","layout":"editorial","font":"serif","particle":"embers"},
]


SUBJ_KW = {
    "영어":["빈칸 추론","EBS 연계","순서·삽입","어법·어휘"],
    "수학":["수1·수2","미적분","확률과 통계","킬러 문항"],
    "국어":["독해력","문학","비문학","화법과 작문"],
    "사회":["생활과 윤리","한국지리","세계사","경제"],
    "과학":["물리학","화학","생명과학","지구과학"],
}

# ── 배경 이미지 키워드 맵 (대폭 강화) ──────────
KO_BG = {
    "야구장":"baseball stadium night crowd","야구":"baseball stadium crowd",
    "경기장":"sports arena stadium","축구장":"soccer field stadium night",
    "축구":"soccer pitch grass","농구장":"basketball court arena",
    "스포츠":"sports stadium action","관중":"crowd stadium lights",
    "군중":"crowd people busy","응원":"crowd cheering stadium",
    "함성":"crowd stadium cheering","선수":"athlete action sport",
    "사이버펑크":"cyberpunk neon city rain","네온":"neon lights night city",
    "도시":"city skyline night","시내":"city street night urban",
    "번화가":"busy city street night","골목":"alley urban city night",
    "루프탑":"rooftop city night","밤거리":"street night city",
    "밤":"night city dark","야경":"city night skyline",
    "극장":"cinema theater dark","영화관":"cinema theater dark",
    "공연장":"concert stage lights","카페":"cafe coffee interior",
    "지하철":"subway underground train","기차":"train railway motion",
    "공항":"airport terminal modern","빌딩":"skyscraper glass modern",
    "벚꽃":"cherry blossom spring","단풍":"autumn leaves forest",
    "숲":"forest trees misty","겨울":"winter snow landscape",
    "눈":"snow winter white","오로라":"aurora northern lights",
    "바다":"ocean sea waves","해변":"beach ocean sand",
    "산":"mountain peak dramatic","강":"river landscape scenic",
    "호수":"lake reflection calm","하늘":"sky clouds dramatic",
    "노을":"sunset golden sky","새벽":"dawn misty morning",
    "안개":"fog mist atmospheric","구름":"clouds sky dramatic",
    "비":"rain street wet","폭풍":"storm lightning dramatic",
    "번개":"lightning storm dark","먹구름":"storm clouds dramatic",
    "꽃":"flowers nature colorful","장미":"roses red romantic",
    "도서관":"library books interior","책":"books library reading",
    "교실":"classroom school","칠판":"chalkboard classroom",
    "사찰":"temple zen peaceful","학교":"school building campus",
    "강의실":"lecture hall university","캠퍼스":"university campus building",
    "우주":"space galaxy nebula","별":"stars night milky way",
    "은하":"galaxy space cosmos","달":"moon night sky",
    "이집트":"egypt pyramid desert","사막":"desert sand dunes",
    "건축":"architecture brutalist concrete","고딕":"gothic dark architecture",
    "불꽃":"fire flames dark","연기":"smoke dark moody",
    "빈티지":"vintage retro film","흑백":"monochrome black white",
    "앰버":"amber golden warm dark","골드":"gold luxury dark",
    "먹빛":"dark ink atmosphere","형광":"neon fluorescent dark",
    "에시드":"neon green dark abstract","미래":"futuristic technology sci-fi",
    "에펠탑":"eiffel tower paris night","파리":"paris france city",
    "뉴욕":"new york city skyline","도쿄":"tokyo japan night",
    "런던":"london city landmark","홍콩":"hong kong city skyline",
    "집중":"focus study desk lamp","수험생":"student study desk night",
    "열정":"fire passion dramatic","고요":"peaceful calm zen",
    "사람 많은":"crowd people busy street","도전":"mountain climbing summit",
    "baseball":"baseball stadium","soccer":"soccer field",
    "library":"library books","space":"space galaxy",
    "fire":"fire flames","neon":"neon lights",
    "ocean":"ocean waves","crowd":"crowd people busy",
    "city":"city skyline night","paris":"paris france eiffel",
    "tokyo":"tokyo japan night","mountain":"mountain dramatic",
    "forest":"forest trees","desert":"desert sand",
    "snow":"snow winter","rain":"rain street",
    "storm":"storm lightning","night":"night city dark",
    "vintage":"vintage retro","abstract":"abstract art colorful",
}

# ══════════════════════════════════════════════════════
# 유틸
# ══════════════════════════════════════════════════════
def strip_hanja(text: str) -> str:
    if not isinstance(text, str): return str(text) if text is not None else ""
    result = []
    for ch in text:
        cp = ord(ch)
        if 0x4E00 <= cp <= 0x9FFF: continue
        if 0x3400 <= cp <= 0x4DBF: continue
        result.append(ch)
    return "".join(result).strip()

def clean_obj(obj):
    if isinstance(obj, str): return strip_hanja(obj)
    if isinstance(obj, dict): return {k: clean_obj(v) for k,v in obj.items()}
    if isinstance(obj, list): return [clean_obj(i) for i in obj]
    return obj

def safe_json(raw: str) -> dict:
    """마크다운이나 불필요한 텍스트가 섞여 있어도 순수 JSON 객체만 추출"""
    # 처음 '{' 와 마지막 '}' 사이의 텍스트만 추출
    start = raw.find('{')
    end = raw.rfind('}')
    
    if start == -1 or end == -1 or start > end:
        raise ValueError(f"JSON 객체를 찾을 수 없습니다.\n원본: {raw[:200]}")
        
    s = raw[start:end+1]
    
    # 줄바꿈 처리 및 찌꺼기 문자 제거
    s = s.replace('\n', ' ').replace('\r', '')
    
    # Llama 모델이 가끔 남기는 문법 오류(마지막 항목 뒤의 쉼표) 강제 수정
    s = re.sub(r",\s*}", "}", s)
    s = re.sub(r",\s*]", "]", s)
    
    try:
        return clean_obj(json.loads(s))
    except Exception as e:
        raise ValueError(f"JSON 파싱 실패: {e}\n수정된 문자열: {s[:200]}")
    candidate = s[:end_idx+1]
    def _try(x):
        try: return clean_obj(json.loads(x))
        except Exception: return None
    r = _try(candidate)
    if r: return r
    r = _try(candidate.replace("\n"," ").replace("\r",""))
    if r: return r
    # 마지막 수단: 일반적인 JSON 수리 시도
    fixed = re.sub(r",\s*}", "}", candidate)
    fixed = re.sub(r",\s*]", "]", fixed)
    r = _try(fixed)
    if r: return r
    raise ValueError(
        f"AI 응답 파싱 실패\n"
        f"원인: JSON 형식 오류 (AI가 올바른 형식으로 응답하지 않음)\n"
        f"해결: 다시 시도해주세요 (모델이 간헐적으로 실패함)\n"
        f"원본 (처음 200자): {raw[:200]}"
    )

def fetch_pixabay_url(query: str) -> str:
    """Pixabay API로 실사 배경 이미지 URL 반환. 키 없으면 빈 문자열."""
    key = st.session_state.get("pixabay_key", "").strip()
    if not key:
        return ""
    if not isinstance(st.session_state.bg_cache, dict):
        st.session_state.bg_cache = {}
    if query in st.session_state.bg_cache:
        return st.session_state.bg_cache[query]
    try:
        r = requests.get(
            "https://pixabay.com/api/",
            params={
                "key": key, "q": query, "image_type": "photo",
                "orientation": "horizontal", "per_page": 20,
                "safesearch": "true", "min_width": 1280, "order": "popular"
            },
            timeout=8,
        )
        if r.ok:
            hits = r.json().get("hits", [])
            if hits:
                hit = random.choice(hits[:min(len(hits), 10)])
                url = hit.get("largeImageURL") or hit.get("webformatURL", "")
                if url:
                    st.session_state.bg_cache[query] = url
                    return url
    except Exception:
        pass
    return ""


def build_bg_url(mood: str) -> str:
    """무드 → 배경 이미지 URL. Pixabay 우선, 없으면 picsum fallback."""
    if not mood:
        return ""
    text = mood.lower()
    found = []
    # 1단계: KO_BG 딕셔너리 매칭 (긴 키워드 우선)
    for ko, en in sorted(KO_BG.items(), key=lambda x: -len(x[0])):
        if ko.lower() in text:
            found = en.split()
            break
    # 2단계: 영어 단어 직접 추출 (3글자 이상으로 완화)
    if not found:
        eng = [w for w in re.findall(r"[a-zA-Z]{3,}", mood)
               if w.lower() not in ("this","that","with","from","have","been","very","some")]
        found.extend(eng[:3])
    # 3단계: 한글 첫 글자 계열로 다양한 fallback
    if not found:
        first = mood.strip()[:1]
        char_map = {
            "시":"city urban street","도":"city urban night",
            "밤":"night dark city","사":"people crowd busy",
            "건":"building architecture modern","자":"nature landscape outdoor",
            "바":"ocean sea waves","하":"sky clouds dramatic",
            "학":"study desk lamp focus","수":"water nature calm",
            "열":"fire passion energy","고":"ancient history stone",
            "새":"dawn morning misty","빌":"building skyscraper glass",
        }
        found = char_map.get(first, "atmospheric dramatic moody").split()
    core = list(dict.fromkeys(t.strip() for t in found))[:3]
    query = " ".join(core)
    pix = fetch_pixabay_url(query)
    if pix:
        return pix
    # picsum fallback — mood 전체 해시로 다양성 보장
    seed = abs(hash(mood)) % 9999
    return f"https://picsum.photos/seed/{seed}/1920/1080"


# ══════════════════════════════════════════════════════
# AI 호출
# ══════════════════════════════════════════════════════
def call_ai(prompt: str, system: str = "", max_tokens: int = 2000) -> str:
    key = st.session_state.api_key.strip()
    if not key:
        raise ValueError("API 키가 없습니다. 사이드바에서 gsk_... 키를 입력해주세요.")
    messages = []
    sys_parts = [system] if system else []
    sys_parts.append("Return ONLY valid JSON. No markdown. No extra text. Never use Chinese characters. Write everything in Korean only.")
    messages.append({"role":"system","content":"\n\n".join(sys_parts)})
    messages.append({"role":"user","content":prompt})
    last_err = None
    for model in GROQ_MODELS:
        try:
            resp = requests.post(
                GROQ_URL,
                headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
                json={"model":model,"messages":messages,"max_tokens":max_tokens,"temperature":0.75},
                timeout=60,
            )
        except Exception as e:
            last_err = Exception(f"네트워크 오류: {e}"); continue
        if resp.status_code == 401:
            raise Exception("🔑 API 키 오류 — console.groq.com에서 확인해주세요.")
        if resp.status_code == 429:
            last_err = Exception(f"⏳ 한도 초과 ({model})"); time.sleep(2); continue
        if not resp.ok:
            try: msg = resp.json().get("error",{}).get("message",resp.text[:150])
            except Exception: msg = resp.text[:150]
            last_err = Exception(f"HTTP {resp.status_code}: {msg}"); continue
        try:
            text = resp.json()["choices"][0]["message"]["content"]
            if text and text.strip(): return text
        except Exception as e:
            last_err = Exception(f"응답 파싱 실패: {e}"); continue
    raise last_err or Exception("모든 모델 실패")

# ══════════════════════════════════════════════════════
# AI 생성 함수
# ══════════════════════════════════════════════════════
# ── 무드별 색상 힌트 (AI 가이드) ──────────────────
MOOD_COLOR_HINTS = {
    "야구장":"배경 #020008 거의검정, 강조색 #FF2244 크림슨레드, 서브 #FF6688, 텍스트 #F5F5FF, 레이아웃 typographic, 폰트 Black Han Sans bold",
    "야구":"배경 #030008 다크, 강조색 #FF2244 레드, 레이아웃 typographic, 폰트 bold sans",
    "경기장":"배경 #020008, 강조색 #FF4400 오렌지레드, 레이아웃 typographic",
    "축구장":"배경 #041200 극다크그린, 강조색 #00FF6A 형광그린 또는 #FFFFFF 화이트, 텍스트 #F0FFF0 밝은민트, 레이아웃 typographic, 폰트 Black Han Sans, 배경이미지 football+pitch+floodlight+night",
    "축구":"배경 #051505 다크그린블랙, 강조색 #7CFC00 잔디그린 또는 #FF4400 레드, 텍스트 #F5FFF5, 레이아웃 typographic",
    "사이버펑크":"배경 #020008 극도어두움, 강조색 #A855F7 보라+#06B6D4 사이언, 레이아웃 typographic, 폰트 Orbitron",
    "네온":"배경 #030308, 강조색 #AAFF00 네온그린 또는 #FF00FF 마젠타, 레이아웃 typographic",
    "이집트":"배경 #0A0600 다크앰버, 강조색 #C8975A 골드, 서브 #F5C842, 레이아웃 editorial_bold",
    "황금":"배경 #080400 거의검정, 강조색 #F59E0B 앰버골드, 레이아웃 immersive",
    "도서관":"배경 #060300 다크세피아, 강조색 #C8975A 골드, 레이아웃 editorial_bold",
    "책":"배경 #080400, 강조색 #C8975A 골드/세피아, 레이아웃 editorial_bold",
    "오로라":"배경 #020810 극야, 강조색 #06B6D4 청록+#A855F7 보라, 레이아웃 immersive",
    "우주":"배경 #030712 우주흑, 강조색 #7C3AED 보라, 레이아웃 typographic",
    "불꽃":"배경 #0D0705, 강조색 #FF4500 파이어오렌지, 레이아웃 typographic",
    "벚꽃":"배경 #FBF6F4 밝은분홍, 강조색 #E8386D, 레이아웃 editorial_bold",
    "겨울":"배경 #F0F4F8 밝은, 강조색 #1E40AF 겨울블루, 레이아웃 split",
    "에시드":"배경 #030703, 강조색 #AAFF00 에시드그린, 레이아웃 typographic, btn-p색 검정",
    "ABPS":"배경 #030703 순수블랙, 강조색 #AAFF00 형광그린, 폰트 Space Grotesk, 레이아웃 typographic",
    "흑백":"배경 #F5F5F0 오프화이트, 강조색 #1A1A1A, 레이아웃 billboard, 폰트 Space Grotesk",
    "빈티지":"배경 #0C0A06 세피아다크, 강조색 #C8975A, 레이아웃 editorial_bold",
}

def gen_concept(seed: dict) -> dict:
    mood = seed.get("mood","")
    ptype = st.session_state.get("purpose_type", "신규 커리큘럼")
    ptype_hint = PURPOSE_THEME_HINTS.get(ptype, "")   # ← 추가
    # 무드 키워드 → 색상 힌트 찾기
    color_hint = ""
    for kw, hint in MOOD_COLOR_HINTS.items():
        if kw.lower() in mood.lower():
            color_hint = f"\n\n⚠️ 색상 필수 지침: {hint}"
            break
    lg = {"brutal":"sharp 0px radius, heavy uppercase, raw contrast, offset shadows",
          "editorial":"serif italic, generous whitespace, asymmetric grid",
          "minimal":"extreme whitespace, thin weights, single accent",
          "magazine":"mixed type scales, editorial grid, ruled lines",
          "immersive":"full-bleed dark, glowing accents, depth layers",
          "organic":"rounded 16-24px, natural tones",
          "modern":"clean grid, 8-12px radius",
          "mono":"monospace terminal, grid-based"}.get(seed.get("layout","auto"),"choose best fit")
    fg = {"serif":"Cormorant Garamond or Playfair Display",
          "sans":"Space Grotesk or Plus Jakarta Sans",
          "display":"Bebas Neue or Black Han Sans",
          "mono":"Space Grotesk or IBM Plex Mono",
          "auto":"choose boldly based on mood"}.get(seed.get("font","auto"),"choose boldly")
    prompt = f"""한국 교육 랜딩페이지 RADICAL 디자이너. 아래 무드를 완벽하게 반영한 파격적 디자인 생성.

무드: "{mood}"
레이아웃 타입: {seed.get("layout","auto")} — {lg}
폰트 방향: {fg}
파티클: {seed.get("particle","none")}
⚠️ 페이지 목적 필수: {ptype_hint}
{color_hint}

디자인 규칙:
- 색상은 무드와 100% 일치해야 함 (야구장=짙은레드/블랙, 에시드=블랙/형광그린, 벚꽃=분홍/흰색 등)
- ⚠️ 대비(contrast) 필수: bg가 어두우면(#000~#333) textHex는 반드시 밝게(#E0 이상), bg가 밝으면(#EEE~#FFF) textHex는 어둡게(#111~#333). 배경과 텍스트 계열이 비슷하면 절대 안 됨
- ⚠️ c1(강조색)은 bg 위에서 확실히 눈에 띄는 색이어야 함 — bg와 같은 계열 금지
- displayFont: 반드시 Google Fonts에 실제로 존재하는 폰트만. 권장: 'Black Han Sans'(한국어 두껍), 'Noto Sans KR', 'Nanum Gothic', 'Bebas Neue'(영문), 'Space Grotesk'(영문)
- 존재하지 않는 폰트명 절대 금지 (예: 'Korean Display', 'Bold Korean' 등 실제 없는 폰트)
- heroStyle: "typographic"(배경색+거대타이포), "cinematic"(다크포토+영화), "billboard"(초대형텍스트), "editorial_bold"(에디토리얼), "split"(2컬럼), "immersive"(풀스크린포토) 중 무드에 맞는 것
- 어두운 테마는 c4와 bg가 완전 다른 색이어야 함 (c4=가장어두운 bg=약간밝은)
- extraCSS 내부 따옴표는 반드시 작은따옴표(') 사용

JSON만 반환 (한 줄, extraCSS 필드 제외):
{{"name":"2-4글자+이모지","dark":true,"heroStyle":"typographic","c1":"#hex","c2":"#hex","c3":"#hex","c4":"#hex","bg":"#hex","bg2":"#hex","bg3":"#hex","textHex":"#hex","textRgb":"r,g,b","bdAlpha":"rgba(r,g,b,.15)","displayFont":"Google Font name","bodyFont":"Noto Sans KR","fontWeights":"400;700;900","displayFontWeights":"400;700","borderRadiusPx":0,"btnBorderRadiusPx":2,"particle":"{seed.get('particle','none')}","ctaGradient":"linear-gradient(135deg,#hex,#hex)"}}"""
    result = safe_json(call_ai(prompt, max_tokens=1400))
    # extraCSS 기본값 보정
    if not result.get("extraCSS") or len(result.get("extraCSS","")) < 30:
        result["extraCSS"] = ".sec{padding:clamp(60px,8vw,100px) clamp(28px,6vw,72px)}.card{border-radius:var(--r,4px)}"
    # 이름 검증
    name = result.get("name","")
    generic = ["한국","교육","랜딩","페이지","강사","수능","학습","공부","스터디","강의"]
    if not name or any(g in name for g in generic) or len(name) > 12:
        mood_word = mood.split()[0][:4] if mood else "NEW"
        result["name"] = mood_word + " 🎨"
    # particle 자동 추론
    mood_l = mood.lower()
    if result.get("particle","none") == "none":
        if any(k in mood_l for k in ["눈","겨울","snow","사찰"]): result["particle"] = "snow"
        elif any(k in mood_l for k in ["벚꽃","봄","꽃"]): result["particle"] = "petals"
        elif any(k in mood_l for k in ["우주","별","cosmos"]): result["particle"] = "stars"
        elif any(k in mood_l for k in ["불꽃","파이어","ember"]): result["particle"] = "embers"
        elif any(k in mood_l for k in ["황금","gold","이집트","앰버"]): result["particle"] = "gold"
        elif any(k in mood_l for k in ["단풍","낙엽","숲"]): result["particle"] = "leaves"
    result = _ensure_contrast(result)
    return result


def _get_instructor_context() -> str:
    ip = st.session_state.get("inst_profile") or {}
    name = st.session_state.instructor_name
    subj = st.session_state.subject
    if not ip.get("found") or not name:
        return f"강사명: {name} | 과목: {subj}" if name else f"과목: {subj}"
    parts = [f"강사: {name} ({subj})"]
    if ip.get("bio"):        parts.append(f"이력: {ip['bio']}")
    if ip.get("slogan"):     parts.append(f"슬로건: \"{ip['slogan']}\"")
    methods = [m for m in (ip.get("signatureMethods") or []) if m and m != "없음"]
    if methods:              parts.append(f"고유 학습법: {', '.join(methods)}")
    if ip.get("teachingStyle"): parts.append(f"강의 스타일: {ip['teachingStyle']}")
    if ip.get("desc"):       parts.append(f"차별점: {ip['desc']}")
    return "\n".join(parts)


def gen_copy(ctx: str, ptype: str, tgt: str, plabel: str) -> dict:
    inst_ctx = _get_instructor_context()
    
    schemas = {
        "신규 커리큘럼": '{"bannerSub":"10자이내","bannerTitle":"20자이내","brandTagline":"페이지 컨셉을 관통하는 브랜드 문구 1문장","bannerLead":"60-90자 수험생 고민을 찌르는 리드","bannerTags":["키워드1","키워드2","키워드3"],"ctaCopy":"10자이내","ctaTitle":"CTA 제목","ctaSub":"30자이내","ctaBadge":"15자이내","statBadges":[],"introTitle":"20자이내","introDesc":"80-120자 강사만의 차별점","introBio":"강사 학습법 포함 60자이내","introBadges":[],"whyTitle":"20자이내","whySub":"30자이내","whyReasons":[["이모지","12자제목","60자 구체적 설명"],["이모지","12자","60자"],["이모지","12자","60자"]],"curriculumTitle":"20자이내","curriculumSub":"30자이내","curriculumSteps":[["01","8자제목","학생 입장에서 50자 이상 설명","기간"],["02","8자","50자 이상","기간"],["03","8자","50자 이상","기간"],["04","8자","50자 이상","기간"]],"targetTitle":"20자이내","targetItems":["이런 학생을 대상으로 하는지 40자 상황 묘사","항목2 40자","항목3 40자","항목4 40자"],"reviews":[["생생한 인용문 50-70자","이름","변화뱃지"],["50-70자 인용문","이름","뱃지"],["50-70자 인용문","이름","뱃지"]],"faqs":[["구체적 질문15자","명쾌한 답변 50자이상"],["질문","50자 답변"],["질문","50자 답변"]],"videoTitle":"영상 섹션 제목 20자","videoSub":"40자 설명","videoTag":"OFFICIAL TRAILER","baTitle":"수강 전/후 비교 제목","baSub":"30자","baBeforeItems":["수강 전 학생 고민 40자","고민2 40자","고민3 40자"],"baAfterItems":["수강 후 변화 40자","변화2 40자","변화3 40자"],"methodTitle":"학습법 시각화 제목","methodSub":"30자","methodSteps":[{"step":"STEP 01","label":"단계명","desc":"45자이상"},{"step":"STEP 02","label":"단계명","desc":"45자이상"},{"step":"STEP 03","label":"단계명","desc":"45자이상"}],"pkgTitle":"구성 안내 제목","pkgSub":"30자","packages":[{"icon":"📗","name":"구성명","desc":"구성 설명 40자이상","badge":"필수"},{"icon":"📖","name":"구성명","desc":"40자이상","badge":"포함"},{"icon":"🎯","name":"구성명","desc":"40자이상","badge":"포함"},{"icon":"💬","name":"구성명","desc":"40자이상","badge":"특전"}]}',
        "이벤트": '{"bannerSub":"10자","bannerTitle":"20자","brandTagline":"이벤트 분위기를 담은 한 문장","bannerLead":"60-80자 긴박감 있는 리드","bannerTags":["이벤트특징1","이벤트특징2","이벤트특징3"],"ctaCopy":"10자","ctaTitle":"CTA","ctaSub":"30자","ctaBadge":"15자","statBadges":[],"eventTitle":"20자","eventDesc":"50자이상","eventDetails":[["📅","이벤트 기간","날짜"],["🎯","대상","값"],["💰","혜택","값"]],"benefitsTitle":"20자","eventBenefits":[{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"01"},{"icon":"이모지","title":"혜택명","desc":"50자","badge":"8자","no":"02"},{"icon":"이모지","title":"혜택명","desc":"50자","badge":"8자","no":"03"}],"deadlineTitle":"20자","deadlineMsg":"70자 긴박감","reviews":[["50-70자 구체적 인용문","이름","뱃지"],["인용문","이름","뱃지"],["인용문","이름","뱃지"]]}',
        "기획전": '{"festHeroTitle":"20자","festHeroCopy":"30자","festHeroSub":"50자이상","brandTagline":"기획전 분위기를 담은 한 문장","festHeroStats":[["수치","라벨"],["수치","라벨"],["수치","라벨"],["수치","라벨"]],"festLineupTitle":"20자","festLineupSub":"40자","festLineup":[{"name":"강사명","tag":"분야8자","tagline":"40자","badge":"8자","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"40자","badge":"뱃지","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"40자","badge":"뱃지","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"40자","badge":"뱃지","emoji":"이모지"}],"festBenefitsTitle":"20자","festBenefits":[{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"01"},{"icon":"이모지","title":"혜택명","desc":"50자","badge":"8자","no":"02"},{"icon":"이모지","title":"혜택명","desc":"50자","badge":"8자","no":"03"},{"icon":"이모지","title":"혜택명","desc":"50자","badge":"8자","no":"04"}],"festCtaTitle":"CTA제목","festCtaSub":"50자이상"}',
    }

    purpose_specific_rule = ""
    if ptype == "이벤트":
        purpose_specific_rule = (
            "⚠️ [!!! 가장 중요한 이벤트 페이지 절대 규칙 !!!]\n"
            f"1. 제목(bannerTitle)은 반드시 다음 사용자가 입력한 맥락을 바탕으로 작성하세요: '{ctx}'\n"
            "2. 'KISS Logic'이나 강사의 정규 커리큘럼 명칭을 제목(bannerTitle)에 **절대 포함하지 마세요**.\n"
            "3. bannerTags는 과목(어법, 빈칸)이 아니라, 이벤트 전용 혜택 단어(예: 기간한정, 전원증정, 모의고사 등)로 3개 작성하세요.\n"
        )
    elif ptype == "기획전":
        purpose_specific_rule = (
            "⚠️ [기획전 페이지 절대 규칙]\n"
            f"1. 제목(bannerTitle)은 반드시 다음 사용자가 입력한 맥락을 바탕으로 작성하세요: '{ctx}'\n"
        )
    else:
        purpose_specific_rule = "⚠️ [신규 커리큘럼 규칙]\n1. 강사의 대표 강좌명이나 맥락을 기반으로 제목을 작성하세요."

    tone_instruction = COPY_TONES.get(st.session_state.copy_tone, "")
    prompt = f"""대한민국 최고 수능 교육 랜딩페이지 카피라이터.

{FEW_SHOT_EXAMPLES}

===문구 생성 지침===
위 예시는 스타일 참고용입니다. 절대 베끼지 말고 [페이지 맥락]을 최우선으로 반영하여 창작하세요.

===강사 정보===
{inst_ctx}

===페이지 정보===
맥락: "{ctx if ctx else '이벤트/기획전 안내'}"
목적: {ptype} | 대상: {tgt} | 브랜드: {plabel}
카피 어조: {tone_instruction}

{purpose_specific_rule}

===문구 품질 기준===
1. 강사 고유 커리큘럼명/학습법명을 반영하되, 위 [절대 규칙]에 따라 페이지 목적에 맞게 제목을 가공할 것.
2. 현대적 직접적 어조 — "체계적", "최고의" 같은 올드한 표현 금지
3. 수험생이 지금 느끼는 구체적 고민을 정확히 찌르는 문구
4. 실제처럼 들리는 수강평 (등급 변화, 학습법 언급 포함), 반드시 50자 이상
5. 수치(만족도%, 합격생수) 절대 금지 — statBadges:[], introBadges:[]
6. 한자 절대 금지. 확인되지 않은 수치(%) 지어내지 말 것.
7. ⚠️ 반드시 한국어로만 작성. 영어·독일어·기타 외국어 단어가 섞이면 안 됨 (강사 고유명사 제외)
8. curriculumSteps 설명은 반드시 50자 이상 — 이 단계가 왜 필요한지, 어떻게 달라지는지 학생 입장에서 서술
9. targetItems는 반드시 40자 이상 — 학생의 구체적인 상황과 고민을 담을 것
10. ⚠️ "교수" 절대 금지 — 직함은 반드시 "선생님" 또는 "강사"만 사용
11. ⚠️ 확인되지 않은 정보(학력, 소속, 경력 등) 절대 지어내지 말 것 — 제공된 강사 정보에 있는 내용만 사용
12. bannerLead·introDesc·ctaSub·whyReasons 설명·curriculumSteps 설명은 반드시 충분히 길고 임팩트 있게 작성.
13. whyReasons 3개의 아이콘·제목은 서로 완전히 다른 관점이어야 함
14. brandTagline: 페이지의 컨셉/무드를 담은 독창적 한 문장.
15. ⚠️ [가장 중요한 규칙] 사용자가 '페이지 맥락'에 특정 내용을 적었다면, 예시('KISS Logic' 등)나 기본 강사 정보보다 그 맥락을 1순위로 반영하여 제목과 내용을 작성해야 합니다.
16. bannerTags는 해당 목적(커리큘럼 특징 또는 이벤트 혜택)에 맞는 짧은 키워드로 3~4개 생성.

JSON만 반환:
{schemas.get(ptype, schemas['신규 커리큘럼'])}"""
    return safe_json(call_ai(prompt, max_tokens=3500))

SEC_LAYOUT_VARIANTS = {
    "why": [
        "가로 2컬럼: 왼쪽 고정 타이틀, 오른쪽 스크롤 카드 리스트 (현재 스타일)",
        "세로 풀와이드 3열 그리드: 각 이유를 큰 번호+아이콘+설명 카드로",
        "타임라인 스타일: 세로 중앙선 기준 좌우 교차 배치",
        "배경색 반전 블록: 각 이유가 배경색이 번갈아 바뀌는 풀와이드 스트라이프",
        "아코디언 없이 펼쳐진 Q&A 스타일: 질문형 제목 + 아래 답변",
    ],
    "curriculum": [
        "왼쪽 타임라인 + 오른쪽 단계 카드 (현재 스타일)",
        "수평 스텝퍼: 가로로 나열된 화살표 연결 단계",
        "크게 번호만 보이는 풀스크린 슬라이드 느낌 세로 배치",
        "체크리스트 스타일: 완료 표시 + 단계명 + 기간 뱃지",
        "좌우 지그재그: 홀수 단계 왼쪽, 짝수 단계 오른쪽",
    ],
    "target": [
        "2컬럼 엇갈린 카드 (현재 스타일)",
        "체크마크 리스트: 큰 체크아이콘 + 한 줄 설명",
        "페르소나 카드: 이름·학년·고민이 적힌 사람 카드 형식",
        "NOT/YES 대비형: 왼쪽 '이런 분은 아님', 오른쪽 '이런 분께 딱'",
        "숫자 강조형: 01~04 번호가 매우 크고, 옆에 설명 텍스트",
    ],
    "reviews": [
        "마소너리 그리드 + 첫 카드 풀와이드 강조 (현재 스타일)",
        "트위터/SNS 카드 스타일: 프로필 이니셜 + 멘션 형식",
        "필름스트립: 가로 스크롤 느낌의 카드 나열",
        "큰 인용부호 강조: 배경에 거대한 따옴표, 텍스트 중앙 배치",
        "점수 카드: 별점 그래프 + 변화 수치 강조",
    ],
    "intro": [
        "3컬럼 그리드: 소개/프로필/시그니처 (현재 스타일)",
        "좌우 2분할: 왼쪽 큰 이름+슬로건, 오른쪽 상세",
        "세로 스크롤형: 제목→설명→메서드 순서로 풀와이드",
        "타임라인형 경력: 연도별 주요 커리큘럼 히스토리",
        "임팩트 숫자 강조: 강의 연차, 수강생 수 등 큰 숫자 먼저",
    ],
    "faq": [
        "왼쪽 고정 타이틀 + 오른쪽 아코디언 (현재 스타일)",
        "탭 방식: 카테고리 탭(수강/교재/환불) + 내용",
        "2컬럼 그리드: 질문-답변 쌍을 카드로 나란히",
        "채팅 버블: 질문은 왼쪽 말풍선, 답변은 오른쪽 말풍선",
        "번호 리스트: Q1~Q5를 순서대로 풀와이드 블록으로",
    ],
    "banner": [
        "풀스크린 배경 + 하단 정렬 텍스트 (현재 typographic 스타일)",
        "중앙 정렬 히어로: 제목+리드+버튼이 화면 정중앙",
        "왼쪽 정렬 + 오른쪽 강의 정보 미니카드",
        "초대형 타이포만: 배경색 + 글자만 가득한 임팩트",
        "상단 브랜드바 + 중앙 콘텐츠 + 하단 통계",
    ],
    "cta": [
        "다크 그라디언트 배경 + 중앙 버튼 (현재 스타일)",
        "풀와이드 두 컬럼: 왼쪽 제목, 오른쪽 버튼+서브텍스트",
        "카운트다운 타이머 포함 긴박감 CTA",
        "소셜 프루프 포함: 별점 + 수강생 수 + 버튼",
        "배경 패턴 + 버튼만 크게: 미니멀 CTA",
    ],
}
import random as _random
def _pick_layout_variant(sec_id: str) -> str:
    """섹션 ID에 맞는 랜덤 레이아웃 변형 설명을 반환"""
    variants = SEC_LAYOUT_VARIANTS.get(sec_id, [])
    if not variants:
        return ""
    # 매번 다른 변형 선택 (현재 스타일 제외 가능성 높임)
    weights = [1] + [3] * (len(variants) - 1)  # 첫 번째(현재 스타일) 확률 낮춤
    chosen = _random.choices(variants, weights=weights, k=1)[0]
    return chosen
def gen_section(sec_id: str) -> dict:
    inst_ctx = _get_instructor_context()
    ptype = st.session_state.purpose_type
    
    schemas = {
        "banner": '{"bannerSub":"10자","bannerTitle":"20자","brandTagline":"컨셉을 담은 브랜드 한 문장","bannerLead":"60-90자 수험생이 공감하는 구체적 리드","bannerTags":["키워드1","키워드2","키워드3"],"ctaCopy":"10자","statBadges":[]}',
        "intro":  '{"introTitle":"20자","introDesc":"80-120자 강사 철학과 차별점","introBio":"강사 학습법 포함 60자","introBadges":[]}',
        "why":    '{"whyTitle":"20자","whySub":"30자","whyReasons":[["이모지","12자","학생 입장에서 구체적 설명 60자"],["이모지","12자","60자"],["이모지","12자","60자"]]}',
        "curriculum": '{"curriculumTitle":"20자","curriculumSub":"30자","curriculumSteps":[["01","8자","이 단계 통해 무엇이 달라지는지 50자 이상 설명","기간"],["02","8자","50자 이상","기간"],["03","8자","50자 이상","기간"],["04","8자","50자 이상","기간"]]}',
        "target": '{"targetTitle":"20자","targetItems":["이런 학생을 위한 40-50자 구체적 상황","항목2 40자","항목3 40자","항목4 40자"]}',
        "reviews": '{"reviews":[["지금도 쓸 것 같은 생생한 50-70자 인용문, 구체적 점수·방법 언급","이름","뱃지"],["50-70자 인용문","이름","뱃지"],["50-70자 인용문","이름","뱃지"]]}',
        "faq":    '{"faqs":[["15자 구체적 질문","명쾌한 답변 50자이상"],["질문","50자 이상 답변"],["질문","50자 이상 답변"]]}',
        "cta":    '{"ctaTitle":"CTA제목","ctaSub":"40자이상 수강신청 동기부여 문구","ctaCopy":"10자","ctaBadge":"15자"}',
        "event_overview": '{"eventTitle":"20자","eventDesc":"50자이상 이벤트 핵심 설명","eventDetails":[["📅","이벤트 기간","날짜"],["🎯","대상","값"],["💰","혜택","값"]]}',
        "event_benefits": '{"benefitsTitle":"20자","eventBenefits":[{"icon":"이모지","title":"혜택명","desc":"50자이상 혜택 설명","badge":"8자","no":"01"},{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"02"},{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"03"}]}',
        "event_deadline": '{"deadlineTitle":"마감 제목 15자","deadlineMsg":"70자이상 긴박감 있는 마감 안내 문구, 학생 심리 자극","ctaCopy":"10자"}',
        "fest_hero":     '{"festHeroTitle":"20자","festHeroCopy":"30자","festHeroSub":"50자이상","brandTagline":"기획전 분위기 한 문장","festHeroStats":[["수치","라벨"],["수치","라벨"]]}',
        "fest_lineup":   '{"festLineupTitle":"20자","festLineupSub":"40자","festLineup":[{"name":"강사명","tag":"8자","tagline":"40자 소개","badge":"8자","emoji":"이모지"},{"name":"강사명","tag":"8자","tagline":"40자","badge":"8자","emoji":"이모지"},{"name":"강사명","tag":"8자","tagline":"40자","badge":"8자","emoji":"이모지"},{"name":"강사명","tag":"8자","tagline":"40자","badge":"8자","emoji":"이모지"}]}',
        "fest_benefits": '{"festBenefitsTitle":"20자","festBenefits":[{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"01"},{"icon":"이모지","title":"혜택명","desc":"50자","badge":"8자","no":"02"},{"icon":"이모지","title":"혜택명","desc":"50자","badge":"8자","no":"03"},{"icon":"이모지","title":"혜택명","desc":"50자","badge":"8자","no":"04"}]}',
        "fest_cta":      '{"festCtaTitle":"CTA 제목 20자","festCtaSub":"50자이상 통합신청 동기부여 문구"}',
        "video":         '{"videoTitle":"영상 섹션 제목 20자","videoSub":"영상 설명 40자","videoTag":"OFFICIAL TRAILER","videoUrl":""}',
        "before_after":  '{"baTitle":"수강 전후 비교 제목 20자","baSub":"30자 서브","baBeforeItems":["수강 전 학생이 겪는 구체적 문제 40자","문제2 40자","문제3 40자"],"baAfterItems":["수강 후 달라지는 점 40자","변화2 40자","변화3 40자"]}',
        "method":        '{"methodTitle":"학습법 제목 20자","methodSub":"30자","methodSteps":[{"step":"STEP 01","label":"단계명","desc":"이 단계에서 무엇을 어떻게 하는지 40자이상"},{"step":"STEP 02","label":"단계명","desc":"40자이상"},{"step":"STEP 03","label":"단계명","desc":"40자이상"}]}',
        "package":       '{"pkgTitle":"구성 안내 제목 20자","pkgSub":"30자","packages":[{"icon":"📗","name":"구성명","desc":"구성 설명 40자이상","badge":"필수"},{"icon":"📖","name":"구성명","desc":"40자이상","badge":"포함"},{"icon":"🎯","name":"구성명","desc":"40자이상","badge":"포함"},{"icon":"💬","name":"구성명","desc":"40자이상","badge":"특전"}]}',
    }
    
    purpose_specific_rule = ""
    if sec_id == "banner":
        if ptype == "이벤트":
            purpose_specific_rule = "⚠️ [!!! 절대 규칙 !!!] 제목에 'KISS Logic' 등 강좌명을 절대 쓰지 마세요. 이벤트 성격(예: 3월 학평 특강, 기대평)에 맞는 제목만 출력하세요. bannerTags는 이벤트용 단어(기간한정, 무료제공 등)로 작성하세요."
    
    sec_name = SEC_LABELS.get(sec_id, sec_id)
    schema = schemas.get(sec_id, '{"title":"제목","desc":"설명"}')
    prompt = f"""수능 교육 카피라이터. "{sec_name}" 섹션만 새롭게 생성.

{FEW_SHOT_EXAMPLES}

위 예시를 절대 베끼지 마세요. 강사와 과목에 맞게 완전히 새로운 문구로 작성.

{inst_ctx}
과목: {st.session_state.subject} | 브랜드: {st.session_state.purpose_label}
카피 어조: {COPY_TONES.get(st.session_state.copy_tone, "")}

{purpose_specific_rule}

규칙: 한자 금지, 수치 금지, 반드시 순수 한국어로만 작성. "교수" 절대 금지.
아래 JSON 형식만 반환. 마크다운 금지:
{schema}"""
    last_err = None
    for _attempt in range(3):
        try:
            return safe_json(call_ai(prompt, max_tokens=900))
        except Exception as e:
            last_err = e
            time.sleep(1)
    raise last_err

# ── 강사 DB ─────────────────────────────────────────
INSTRUCTOR_DB = {
    "이명학": {"found":True,"subject":"영어","platform":"대성마이맥",
        "bio":"대성마이맥 영어 강사. R'gorithm·Syntax·Read N' Logic 시리즈.",
        "slogan":"영어, 논리로 끝낸다","signatureMethods":["R'gorithm","Syntax"],
        "teachingStyle":"구문 분석과 독해 논리 체계적 연결","desc":"R'gorithm으로 지문 구조를 논리적으로 파악"},
    "션티": {"found":True,"subject":"영어","platform":"대성마이맥",
        "bio":"대성마이맥 영어 강사. KISS 시리즈(KISSAVE·KISSCHEMA·KISS Logic).",
        "slogan":"KISS — Keep It Simple, Suneung","signatureMethods":["KISS Logic","KISSAVE","KISSCHEMA"],
        "teachingStyle":"수능 영어 핵심 원리를 KISS로 단순화 반복 훈련","desc":"KISS 시리즈로 처음부터 끝까지 수능 영어 완성"},
    "이미지": {"found":True,"subject":"수학","platform":"대성마이맥",
        "bio":"대성마이맥 수학 강사. 세젤쉬·미친개념·미친기분 시리즈.",
        "slogan":"수학, 미치도록 쉽게","signatureMethods":["세젤쉬","미친개념","미친기분"],
        "teachingStyle":"복잡한 개념을 직관적으로 쉽게","desc":"세젤쉬·미친개념으로 수학 입문자도 따라오게 만드는 강사"},
    "김범준": {"found":True,"subject":"수학","platform":"대성마이맥",
        "bio":"대성마이맥 수학. Starting Block·KICE Anatomy·The Hurdling.",
        "slogan":"수능 수학의 뼈대를 세워라","signatureMethods":["KICE Anatomy","Starting Block","The Hurdling"],
        "teachingStyle":"수능 기출 해부로 출제 원리 파악","desc":"KICE Anatomy로 수능 수학 기출 원리 완전 이해"},
    "김승리": {"found":True,"subject":"국어","platform":"대성마이맥",
        "bio":"대성마이맥 국어. All Of KICE·VIC-FLIX 시리즈.",
        "slogan":"국어, 승리로 끝낸다","signatureMethods":["All Of KICE","VIC-FLIX"],
        "teachingStyle":"수능 국어 출제 원리 파악 후 실전 능력 강화","desc":"All Of KICE로 국어 원리부터 실전까지 완성"},
    "유대종": {"found":True,"subject":"국어","platform":"대성마이맥",
        "bio":"대성마이맥 국어. 인셉션 시리즈·파노라마·O.V.S.",
        "slogan":"국어의 인셉션을 시작하라","signatureMethods":["인셉션","O.V.S","파노라마"],
        "teachingStyle":"인셉션 방식으로 국어 깊이 이해","desc":"인셉션 시리즈로 국어 원리 차근차근 이해"},
}

def search_instructor(name: str, subj: str) -> dict:
    if name in INSTRUCTOR_DB: return INSTRUCTOR_DB[name]
    for db_name, info in INSTRUCTOR_DB.items():
        if name in db_name or db_name in name: return info
    prompt = f"""한국 수능 강사 "{name}" ({subj}). 확실히 아는 정보만. 모르면 빈 문자열. 지어내지 말 것. 한자 금지.
JSON만: {{"found":true,"bio":"1문장","slogan":"","signatureMethods":[],"teachingStyle":"1문장","desc":"1문장"}}"""
    try:
        return safe_json(call_ai(prompt, max_tokens=300))
    except Exception:
        return {"found":True,"bio":f"{subj} 강사","slogan":"","signatureMethods":[],"teachingStyle":"","desc":""}

# ══════════════════════════════════════════════════════
# 테마 리졸버
# ══════════════════════════════════════════════════════
def _hex_luminance(h: str) -> float:
    """간단한 상대 휘도 계산 (0=어두움, 1=밝음)"""
    try:
        h = h.lstrip("#")
        if len(h) == 3: h = "".join(c*2 for c in h)
        r,g,b = int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
        def lin(v): return v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4
        return 0.2126*lin(r)+0.7152*lin(g)+0.0722*lin(b)
    except Exception: return 0.5

def _ensure_contrast(ct: dict) -> dict:
    bg_l  = _hex_luminance(ct.get("bg","#111"))
    tx_l  = _hex_luminance(ct.get("textHex","#fff"))
    ratio = (max(bg_l,tx_l)+0.05)/(min(bg_l,tx_l)+0.05)
    if ratio < 4.5:
        if bg_l < 0.18:
            ct["textHex"] = "#F0F0F0"
            ct["textRgb"] = "240,240,240"
        else:
            ct["textHex"] = "#111111"
            ct["textRgb"] = "17,17,17"
    # 밝은 배경(luminance > 0.4)이면 c1도 어두운 색으로 보정
    if bg_l > 0.4:
        c1_l = _hex_luminance(ct.get("c1","#000"))
        if c1_l > 0.4:
            ct["c1"] = "#0A0A0A"
    return ct

def _cta_text_color(T: dict) -> dict:
    """CTA 그라디언트의 평균 밝기를 계산해 텍스트 색상 자동 결정"""
    cta = T.get("cta", "")
    hexes = re.findall(r'#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})', cta)
    
    if hexes:
        lums = [_hex_luminance("#" + h) for h in hexes]
        avg_lum = sum(lums) / len(lums)
    else:
        avg_lum = 0

    if avg_lum > 0.4:  # 밝은 배경 (예: 형광 연두) → 검정 텍스트로 가독성 확보
        return {
            "txt": "#0A0A0A", "txt70": "rgba(10,10,10,.8)", "txt35": "rgba(10,10,10,.5)",
            "badge_bg": "rgba(0,0,0,.08)", "badge_bd": "rgba(0,0,0,.2)",
            "btn_bg": "#0A0A0A", "btn_col": "#fff",
            "btn2_bg": "rgba(0,0,0,.05)", "btn2_col": "rgba(0,0,0,.8)", "btn2_bd": "rgba(0,0,0,.25)",
        }
    return {  # 어두운 배경 → 흰 텍스트
        "txt": "#fff", "txt70": "rgba(255,255,255,.75)", "txt35": "rgba(255,255,255,.4)",
        "badge_bg": "rgba(255,255,255,.15)", "badge_bd": "rgba(255,255,255,.25)",
        "btn_bg": "#fff", "btn_col": "#0A0A0A",
        "btn2_bg": "rgba(255,255,255,.1)", "btn2_col": "rgba(255,255,255,.9)", "btn2_bd": "rgba(255,255,255,.35)",
    }

def get_theme() -> dict:
    if st.session_state.concept == "custom" and st.session_state.custom_theme:
        ct = _ensure_contrast(st.session_state.custom_theme)
        df  = ct.get("displayFont","Noto Sans KR")
        bf  = ct.get("bodyFont","Noto Sans KR")
        fw  = ct.get("fontWeights","400;700;900")
        dfw = ct.get("displayFontWeights","400;700")
        r   = ct.get("borderRadiusPx",4)
        rb  = ct.get("btnBorderRadiusPx",4)
        tr  = ct.get("textRgb","255,255,255")
        bd  = ct.get("bdAlpha","rgba(255,255,255,.12)")
        # 폰트 이름 정규화 (Black Han Sans는 weight 파라미터 불필요)
        _no_weight_fonts = ["Black Han Sans","Bebas Neue","Orbitron","Nanum Brush Script"]
        if df in _no_weight_fonts:
            fonts = (f"https://fonts.googleapis.com/css2?family={df.replace(' ','+')}",)
            fonts = fonts[0] + f"&family={bf.replace(' ','+')}:wght@{fw}&display=swap"
        else:
            fonts = (f"https://fonts.googleapis.com/css2?family={df.replace(' ','+')}:wght@{dfw}"
                     f"&family={bf.replace(' ','+')}:wght@{fw}&display=swap")
        v = (f"--c1:{ct['c1']};--c2:{ct['c2']};--c3:{ct['c3']};--c4:{ct['c4']};"
             f"--bg:{ct['bg']};--bg2:{ct['bg2']};--bg3:{ct['bg3']};"
             f"--text:{ct['textHex']};--t70:rgba({tr},.7);--t45:rgba({tr},.45);"
             f"--bd:{bd};--fh:'{df}','Noto Serif KR',serif;"
             f"--fb:'{bf}',sans-serif;--r:{r}px;--r-btn:{rb}px;")
        return {"fonts":fonts,"vars":v,"extra_css":ct.get("extraCSS",""),
                "dark":ct.get("dark",True),"heroStyle":ct.get("heroStyle","typographic"),
                "cta":ct.get("ctaGradient",f"linear-gradient(135deg,{ct['c4']},{ct['c1']})"),
                "particle":ct.get("particle","none")}
    t = THEMES.get(st.session_state.concept, THEMES["acid"])
    return {"fonts":t["fonts"],"vars":t["vars"],"extra_css":t.get("extra_css",""),
            "dark":t.get("dark",True),"heroStyle":t.get("heroStyle","typographic"),
            "cta":t.get("cta","linear-gradient(135deg,var(--c4),var(--c1))"),
            "particle":t.get("particle","none")}

# ══════════════════════════════════════════════════════
# BASE CSS — 파격적 업그레이드
# ══════════════════════════════════════════════════════
BASE_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:var(--fb);background:var(--bg);color:var(--text);overflow-x:hidden;-webkit-font-smoothing:antialiased}
#hero{scroll-margin-top:0}
section[id]:not(#hero){scroll-margin-top:64px}
a{text-decoration:none;color:inherit}

/* -- 한국어 줄 맞춤 핵심 규칙 -- */
h1,h2,h3,p,span,div{word-break:keep-all;overflow-wrap:break-word;white-space:normal}
h1,h2,h3{line-height:1.15;letter-spacing:-.04em}
p{line-height:1.9}
/* 카드 내 텍스트 잘림 방지 */
.card *,.rv *{overflow:visible;min-width:0}

/* -- 인트로 애니메이션 -- */
.rv{opacity:0;transform:translateY(32px) scale(.98);transition:opacity .8s cubic-bezier(.16,1,.3,1),transform .8s cubic-bezier(.16,1,.3,1)}
.rv.on{opacity:1;transform:translateY(0) scale(1)}
.d1{transition-delay:.1s}.d2{transition-delay:.22s}.d3{transition-delay:.36s}.d4{transition-delay:.52s}
.rv-left{opacity:0;transform:translateX(-28px);transition:opacity .8s cubic-bezier(.16,1,.3,1),transform .8s cubic-bezier(.16,1,.3,1)}
.rv-left.on{opacity:1;transform:translateX(0)}
.rv-right{opacity:0;transform:translateX(28px);transition:opacity .8s cubic-bezier(.16,1,.3,1),transform .8s cubic-bezier(.16,1,.3,1)}
.rv-right.on{opacity:1;transform:translateX(0)}
@keyframes fadeUp{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
@keyframes pulse-accent{0%,100%{opacity:.6}50%{opacity:1}}

/* -- 버튼 -- */
.btn-p{display:inline-flex;align-items:center;gap:8px;background:var(--c1);color:#fff;
  font-family:var(--fb);font-size:12px;font-weight:800;padding:11px 24px;
  border-radius:var(--r-btn,4px);border:none;cursor:pointer;
  box-shadow:0 4px 24px rgba(0,0,0,.25);
  transition:opacity .15s,transform .15s,box-shadow .15s;text-decoration:none;letter-spacing:.02em;
  white-space:nowrap}
.btn-p:hover{opacity:.88;transform:translateY(-2px);box-shadow:0 8px 32px rgba(0,0,0,.35)}
.btn-s{display:inline-flex;align-items:center;gap:7px;background:transparent;
  color:var(--text);font-family:var(--fb);font-size:14px;font-weight:600;
  padding:13px 24px;border-radius:var(--r-btn,4px);border:1.5px solid var(--bd);
  cursor:pointer;transition:border-color .15s,color .15s;text-decoration:none;white-space:nowrap}
.btn-s:hover{border-color:var(--c1);color:var(--c1)}

/* -- 섹션 기본 -- */
.sec{padding:clamp(60px,8vw,96px) clamp(28px,6vw,80px);position:relative}
.sec.alt{background:var(--bg2)}
.sec+.sec{border-top:1px solid var(--bd)}
.sec+.sec.alt{border-top:none}
.sec.alt+.sec{border-top:none}
.sec-accent-line{display:block;width:48px;height:3px;background:var(--c1);margin-bottom:18px}
.sec-inner{max-width:1200px;margin:0 auto}

/* -- 섹션 구분선 (대각선) -- */
.sec-diag-top::before{
  content:'';position:absolute;top:-40px;left:0;right:0;height:40px;
  background:inherit;
  clip-path:polygon(0 100%,100% 0,100% 100%);z-index:2;
}
.sec-diag-bot::after{
  content:'';position:absolute;bottom:-40px;left:0;right:0;height:40px;
  background:inherit;
  clip-path:polygon(0 0,100% 0,100% 100%);z-index:2;
}

/* -- 태그라인 -- */
.tag-line{display:inline-flex;align-items:center;gap:9px;font-size:9.5px;font-weight:800;
  letter-spacing:.18em;text-transform:uppercase;color:var(--c1);margin-bottom:14px}
.tag-line::before{content:'';display:block;width:24px;height:2px;background:var(--c1)}

/* -- 섹션 타이틀 -- */
.sec-h2{font-family:var(--fh);font-size:clamp(24px,3.5vw,40px);font-weight:900;
  line-height:1.15;letter-spacing:-.04em;color:var(--text);margin-bottom:12px;
  word-break:keep-all;overflow-wrap:break-word}
.sec-sub{font-size:14px;line-height:1.9;color:var(--t70);margin-bottom:36px;
  max-width:560px;word-break:keep-all;overflow-wrap:break-word}

/* -- 카드 -- */
.card{background:var(--bg);border:1px solid var(--bd);border-radius:var(--r,4px);
  padding:24px;transition:transform .25s,box-shadow .25s}
.card:hover{transform:translateY(-4px);box-shadow:0 12px 40px rgba(0,0,0,.12)}

/* -- 강조 숫자 배경 데코 -- */
.num-deco{position:absolute;font-family:var(--fh);font-size:clamp(120px,18vw,220px);
  font-weight:900;line-height:1;opacity:.035;color:var(--c1);pointer-events:none;
  user-select:none;z-index:0}

/* -- 형광 강조 텍스트 -- */
.highlight{background:var(--c1);color:#fff;padding:0 6px;display:inline}

/* -- 타이포그래피 히어로 전용 -- */
.hero-word-accent{
  -webkit-text-stroke:2px var(--c1);
  color:transparent;
  font-family:var(--fh);
}

/* -- 반응형 그리드 안전장치 -- */
@media(max-width:900px){
  .sec{padding:clamp(48px,8vw,72px) clamp(20px,5vw,40px)}
  [style*="grid-template-columns:1fr 1.4fr"],
  [style*="grid-template-columns:1fr 1.6fr"],
  [style*="grid-template-columns:1fr 1.8fr"],
  [style*="grid-template-columns:1.2fr 1fr"],
  [style*="grid-template-columns:1.3fr 1fr"],
  [style*="grid-template-columns:1fr 2fr"]{grid-template-columns:1fr!important}
  [style*="grid-template-columns:repeat(3,1fr)"]{grid-template-columns:1fr 1fr!important}
  [style*="grid-template-columns:repeat(4,1fr)"]{grid-template-columns:1fr 1fr!important}
  [style*="grid-template-columns:1fr 60px 1fr"]{grid-template-columns:1fr!important}
}
@media(max-width:580px){
  [style*="grid-template-columns:1fr 1fr"]{grid-template-columns:1fr!important}
  [style*="grid-template-columns:repeat(2,1fr)"]{grid-template-columns:1fr!important}
}
/* -- 다크/라이트 모드 토글 버튼 -- */
#mode-toggle{
  position:fixed;bottom:80px;right:24px;z-index:9991;
  width:44px;height:44px;border-radius:50%;border:1.5px solid rgba(255,255,255,.2);
  background:rgba(20,20,30,.7);backdrop-filter:blur(12px);
  cursor:pointer;display:flex;align-items:center;justify-content:center;
  font-size:18px;transition:all .2s;box-shadow:0 4px 20px rgba(0,0,0,.3)}
#mode-toggle:hover{transform:scale(1.1);background:rgba(40,40,60,.9)}
/* 라이트 모드 오버라이드 */
body.light-mode{
  --bg:#F5F5F0!important;--bg2:#EBEBEB!important;--bg3:#E0E0E0!important;
  --text:#0A0A0A!important;--t70:rgba(10,10,10,.7)!important;--t45:rgba(10,10,10,.45)!important;
  --bd:rgba(10,10,10,.12)!important;
  --c1:#0A0A0A!important;
  background:var(--bg)!important;color:var(--text)!important}
body.light-mode .card{background:var(--bg)!important;border-color:var(--bd)!important}
body.light-mode #site-nav{background:rgba(245,245,240,.92)!important}
body.light-mode #site-nav a{color:rgba(10,10,10,.65)!important}
body.light-mode #site-nav a:hover{color:#0A0A0A!important}
body.light-mode #mode-toggle{background:rgba(240,240,235,.9)!important;border-color:rgba(0,0,0,.15)!important}
"""


# ══════════════════════════════════════════════════════
# 파티클 JS
# ══════════════════════════════════════════════════════
def _particle_js(particle: str) -> str:
    if particle == "snow":
        return """<style>.snowflake{position:fixed;top:-20px;color:#fff;font-size:1.2em;text-shadow:0 0 8px rgba(180,220,255,.8);animation:snowfall linear infinite;pointer-events:none;z-index:9999;opacity:.8}@keyframes snowfall{0%{transform:translateY(-20px) rotate(0deg);opacity:.8}100%{transform:translateY(110vh) rotate(360deg);opacity:0}}</style><script>(function(){const c=["❄","❅","❆","✦","·"];for(let i=0;i<25;i++){const el=document.createElement("span");el.className="snowflake";el.textContent=c[Math.floor(Math.random()*c.length)];el.style.cssText=`left:${Math.random()*100}vw;font-size:${0.8+Math.random()*1.6}em;animation-duration:${4+Math.random()*8}s;animation-delay:${-Math.random()*8}s;opacity:${0.4+Math.random()*.6}`;document.body.appendChild(el);}})()</script>"""
    if particle == "stars":
        return """<style>.star-p{position:fixed;border-radius:50%;background:#fff;animation:twinkle ease-in-out infinite;pointer-events:none;z-index:9999}@keyframes twinkle{0%,100%{opacity:.15;transform:scale(1)}50%{opacity:1;transform:scale(1.5)}}</style><script>(function(){for(let i=0;i<70;i++){const el=document.createElement("div");el.className="star-p";const s=1+Math.random()*2.5;el.style.cssText=`width:${s}px;height:${s}px;top:${Math.random()*100}vh;left:${Math.random()*100}vw;animation-duration:${1.5+Math.random()*3}s;animation-delay:${-Math.random()*3}s;box-shadow:0 0 ${s*2}px rgba(180,200,255,.9)`;document.body.appendChild(el);}})()</script>"""
    if particle == "petals":
        return """<style>.petal{position:fixed;top:-20px;font-size:1.1em;animation:petalfall linear infinite;pointer-events:none;z-index:9999;opacity:.7}@keyframes petalfall{0%{transform:translateY(-20px) rotate(0deg) translateX(0);opacity:.7}50%{transform:translateY(55vh) rotate(180deg) translateX(30px);opacity:.5}100%{transform:translateY(110vh) rotate(360deg) translateX(-10px);opacity:0}}</style><script>(function(){const p=["🌸","🌺","🌼","✿","❀"];for(let i=0;i<20;i++){const el=document.createElement("span");el.className="petal";el.textContent=p[Math.floor(Math.random()*p.length)];el.style.cssText=`left:${Math.random()*100}vw;font-size:${0.7+Math.random()*1.2}em;animation-duration:${5+Math.random()*8}s;animation-delay:${-Math.random()*8}s`;document.body.appendChild(el);}})()</script>"""
    if particle == "embers":
        return """<style>.ember{position:fixed;bottom:-10px;border-radius:50%;animation:emberrise linear infinite;pointer-events:none;z-index:9999}@keyframes emberrise{0%{transform:translateY(0) translateX(0) scale(1);opacity:.9}50%{transform:translateY(-45vh) translateX(20px) scale(.7);opacity:.6}100%{transform:translateY(-95vh) translateX(-10px) scale(.2);opacity:0}}</style><script>(function(){const c=["#FF4500","#FF8C00","#FFD700","#FF6347"];for(let i=0;i<30;i++){const el=document.createElement("div");el.className="ember";const s=2+Math.random()*4;el.style.cssText=`width:${s}px;height:${s}px;left:${Math.random()*100}vw;background:${c[Math.floor(Math.random()*c.length)]};box-shadow:0 0 ${s}px #FF4500;animation-duration:${3+Math.random()*5}s;animation-delay:${-Math.random()*5}s`;document.body.appendChild(el);}})()</script>"""
    if particle == "gold":
        return """<style>.gold-p{position:fixed;top:-10px;font-size:.9em;animation:goldfall linear infinite;pointer-events:none;z-index:9999}@keyframes goldfall{0%{transform:translateY(-20px) rotate(0deg);opacity:.9}100%{transform:translateY(110vh) rotate(720deg);opacity:0}}</style><script>(function(){const g=["✦","★","◆","·","⬥"];for(let i=0;i<35;i++){const el=document.createElement("span");el.className="gold-p";el.textContent=g[Math.floor(Math.random()*g.length)];el.style.cssText=`left:${Math.random()*100}vw;color:${["#FFD700","#C8975A","#F5C842","#FFA500"][Math.floor(Math.random()*4)]};font-size:${0.5+Math.random()*1}em;animation-duration:${4+Math.random()*6}s;animation-delay:${-Math.random()*6}s;text-shadow:0 0 8px #FFD700`;document.body.appendChild(el);}})()</script>"""
    if particle == "leaves":
        return """<style>.leaf{position:fixed;top:-20px;font-size:1em;animation:leaffall linear infinite;pointer-events:none;z-index:9999}@keyframes leaffall{0%{transform:translateY(-20px) rotate(0deg) translateX(0);opacity:.8}100%{transform:translateY(110vh) rotate(540deg) translateX(40px);opacity:0}}</style><script>(function(){const l=["🍃","🍂","🍁","🌿","🌾"];for(let i=0;i<18;i++){const el=document.createElement("span");el.className="leaf";el.textContent=l[Math.floor(Math.random()*l.length)];el.style.cssText=`left:${Math.random()*100}vw;font-size:${0.8+Math.random()*1.2}em;animation-duration:${5+Math.random()*7}s;animation-delay:${-Math.random()*7}s`;document.body.appendChild(el);}})()</script>"""
    return ""
def _theme_fx(concept: str) -> str:
    """테마별 시그니처 코딩 효과 HTML/JS/CSS"""
    if concept == "acid":
        return '<style>body::after{content:"";position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,.05) 3px,rgba(0,0,0,.05) 4px);pointer-events:none;z-index:9994}@keyframes glitch{0%,78%,100%{clip-path:inset(100% 0 0 0);transform:translateX(0)}79%{clip-path:inset(8% 0 58% 0);transform:translateX(-4px)}81%{clip-path:inset(48% 0 18% 0);transform:translateX(4px)}85%{clip-path:inset(100% 0 0 0)}}h1.st{position:relative}h1.st::before{content:attr(data-g);position:absolute;top:0;left:0;width:100%;height:100%;color:#ff00ff;animation:glitch 5s infinite;pointer-events:none}h1.st::after{content:attr(data-g);position:absolute;top:0;left:0;width:100%;height:100%;color:#00ffff;animation:glitch 5s infinite .3s;pointer-events:none}</style><script>document.querySelectorAll("h1.st").forEach(e=>e.setAttribute("data-g",e.textContent));</script>'
    if concept == "cinematic":
        return '<style>#fg{position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:9994;opacity:.05;mix-blend-mode:overlay}#vg{position:fixed;inset:0;pointer-events:none;z-index:9993;background:radial-gradient(ellipse 85% 65% at 50% 50%,transparent 35%,rgba(0,0,0,.75) 100%)}@keyframes shutter{0%,96%,100%{opacity:1}97%{opacity:.3}98%{opacity:.8}99%{opacity:.1}}body{animation:shutter 12s infinite}</style><canvas id="fg"></canvas><div id="vg"></div><script>(()=>{const c=document.getElementById("fg");if(!c)return;const ctx=c.getContext("2d");function r(){c.width=innerWidth;c.height=innerHeight;}r();addEventListener("resize",r);function g(){const d=ctx.createImageData(c.width,c.height);for(let i=0;i<d.data.length;i+=4){const v=Math.random()*255|0;d.data[i]=d.data[i+1]=d.data[i+2]=v;d.data[i+3]=255;}ctx.putImageData(d,0,0);}g();setInterval(g,60);})();</script>'
    if concept == "stadium":
        return '<style>@keyframes s1{0%{transform:translateX(-120%) rotate(-15deg);opacity:0}8%{opacity:.14}92%{opacity:.14}100%{transform:translateX(220%) rotate(-15deg);opacity:0}}@keyframes s2{0%{transform:translateX(120%) rotate(15deg);opacity:0}8%{opacity:.1}92%{opacity:.1}100%{transform:translateX(-220%) rotate(15deg);opacity:0}}#sp1,#sp2{position:fixed;top:-30%;width:50%;height:160%;background:conic-gradient(from 90deg,transparent 155deg,rgba(255,255,255,.08) 155deg 195deg,transparent 195deg);pointer-events:none;z-index:9993}#sp1{left:0;animation:s1 7s ease-in-out infinite}#sp2{right:0;animation:s2 9s ease-in-out 1.5s infinite}</style><div id="sp1"></div><div id="sp2"></div>'
    if concept == "cosmos":
        return '<style>@keyframes mt{0%{transform:translate(0,0) rotate(45deg);opacity:0}5%{opacity:1}100%{transform:translate(600px,600px) rotate(45deg);opacity:0}}@keyframes nb{0%,100%{opacity:.05;transform:scale(1)}50%{opacity:.12;transform:scale(1.08)}}.me{position:fixed;width:2px;height:70px;background:linear-gradient(to bottom,rgba(255,255,255,0),rgba(255,255,255,.9));pointer-events:none;z-index:9993}#nb1,#nb2{position:fixed;border-radius:50%;pointer-events:none;z-index:9992;filter:blur(60px)}#nb1{top:5%;left:55%;width:600px;height:400px;background:radial-gradient(ellipse,rgba(124,58,237,.18),rgba(6,182,212,.08),transparent 70%);animation:nb 9s ease-in-out infinite}#nb2{top:55%;left:5%;width:450px;height:350px;background:radial-gradient(ellipse,rgba(6,182,212,.12),rgba(124,58,237,.06),transparent 70%);animation:nb 11s ease-in-out 2s infinite}</style><div id="nb1"></div><div id="nb2"></div><script>(()=>{function lm(){const el=document.createElement("div");el.className="me";const d=.8+Math.random()*1.5;el.style.cssText=`top:${Math.random()*40}%;left:${5+Math.random()*60}%;animation:mt ${d}s linear forwards;`;document.body.appendChild(el);setTimeout(()=>{el.remove();setTimeout(lm,2000+Math.random()*6000);},d*1000);}for(let i=0;i<4;i++)setTimeout(lm,i*1800+Math.random()*2000);})();</script>'
    if concept in ("inception", "amber", "luxury"):
        c1 = {"inception":"rgba(45,184,124,.12)","amber":"rgba(245,158,11,.1)","luxury":"rgba(200,151,90,.1)"}.get(concept,"rgba(200,151,90,.1)")
        return f'<style>@keyframes of{{0%,100%{{transform:translateY(0) scale(1);opacity:.06}}50%{{transform:translateY(-50px) scale(1.12);opacity:.13}}}}.lo{{position:fixed;border-radius:50%;pointer-events:none;z-index:9992;background:radial-gradient(circle,{c1},transparent 70%);filter:blur(40px);animation:of ease-in-out infinite}}</style><script>(()=>{{for(let i=0;i<6;i++){{const el=document.createElement("div");el.className="lo";const s=120+Math.random()*200;el.style.cssText=`width:${{s}}px;height:${{s}}px;top:${{5+Math.random()*75}}%;left:${{3+Math.random()*85}}%;animation-duration:${{7+Math.random()*9}}s;animation-delay:${{Math.random()*5}}s;`;document.body.appendChild(el);}}}})();</script>'
    if concept == "fire":
        return '<style>@keyframes flicker{0%,100%{opacity:1}92%{opacity:.65}96%{opacity:.75}}body{animation:flicker 9s infinite}#ml{position:fixed;bottom:0;left:0;right:0;height:4px;background:linear-gradient(90deg,transparent,#FF4500 15%,#FF8C00 50%,#FFD700 70%,#FF4500 85%,transparent);pointer-events:none;z-index:9998;box-shadow:0 0 24px #FF4500,0 0 48px rgba(255,69,0,.3)}</style><div id="ml"></div>'
    if concept == "brutal":
        return '<style>@keyframes hl{0%,88%,100%{opacity:0}89%{opacity:.5;transform:scaleY(1)}91%{opacity:.8;transform:scaleY(3)}95%{opacity:0}}#bhl{position:fixed;left:0;right:0;height:2px;background:#000;pointer-events:none;z-index:9997;animation:hl 6s steps(1) infinite;top:50%}</style><div id="bhl"></div>'
    if concept == "violet_pop":
        return '<style>@keyframes pp{0%{transform:scale(0);opacity:.5}100%{transform:scale(6);opacity:0}}.pc{position:fixed;border-radius:50%;background:rgba(124,58,237,.08);pointer-events:none;z-index:9992;animation:pp 1.2s ease-out forwards}</style><script>document.addEventListener("click",e=>{const el=document.createElement("div");el.className="pc";const s=20;el.style.cssText=`width:${s}px;height:${s}px;left:${e.clientX-s/2}px;top:${e.clientY-s/2}px;`;document.body.appendChild(el);setTimeout(()=>el.remove(),1200);});</script>'
    if concept in ("floral", "sakura"):
        c1 = "rgba(232,56,109,.18)" if concept == "floral" else "rgba(181,48,74,.12)"
        return f'<style>@keyframes ls{{0%,100%{{opacity:0;transform:scale(.4)}}50%{{opacity:.1;transform:scale(1)}}}}.lb{{position:fixed;border-radius:50%;pointer-events:none;z-index:9992;background:radial-gradient(circle,{c1},transparent 70%);filter:blur(25px);animation:ls ease-in-out infinite}}</style><script>(()=>{{for(let i=0;i<5;i++){{const el=document.createElement("div");el.className="lb";const s=80+Math.random()*130;el.style.cssText=`width:${{s}}px;height:${{s}}px;top:${{10+Math.random()*70}}%;left:${{10+Math.random()*75}}%;animation-duration:${{4+Math.random()*5}}s;animation-delay:${{Math.random()*3}}s;`;document.body.appendChild(el);}}}})();</script>'
    if concept == "ocean":
        return '<style>@keyframes wp{0%,100%{opacity:.04}50%{opacity:.08}}#ow{position:fixed;bottom:0;left:0;right:0;height:6px;pointer-events:none;z-index:9993;background:linear-gradient(90deg,transparent,#0EA5E9 20%,#38BDF8 50%,#0EA5E9 80%,transparent);animation:wp 4s ease-in-out infinite;filter:blur(2px)}</style><div id="ow"></div>'
    return ""
# ══════════════════════════════════════════════════════
# 섹션 빌더
# ══════════════════════════════════════════════════════
def _bg_vars(bg_url, dark):
    if not bg_url:
        return {"hero_bg":f"background:var(--bg)","overlay":"","tc":"color:var(--text)",
                "t70c":"color:var(--t70)","c1c":"var(--c1)","bdc":"var(--bd)",
                "card_bg":"rgba(255,255,255,.05)" if dark else "var(--bg)",
                "btn_s":"","top_brd":"var(--bd)","blur":""}
    return {"hero_bg":f"background:var(--bg) url('{bg_url}') center/cover no-repeat",
            "overlay":'<div style="position:absolute;inset:0;background:rgba(0,0,0,0.62);z-index:1;pointer-events:none"></div>',
            "tc":"color:#fff","t70c":"color:rgba(255,255,255,.82)","c1c":"#fff",
            "bdc":"rgba(255,255,255,.28)","card_bg":"rgba(0,0,0,.7)",
            "btn_s":"color:#fff;border-color:rgba(255,255,255,.4)",
            "top_brd":"rgba(255,255,255,.22)","blur":"backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);"}


def sec_banner(d, cp, T):
    sub   = strip_hanja(cp.get("bannerSub", d["subject"]+" 완성"))
    title = strip_hanja(cp.get("bannerTitle", d["purpose_label"]))
    lead  = strip_hanja(cp.get("bannerLead", f"{d['target']}을 위한 커리큘럼"))
    tagline = strip_hanja(cp.get("brandTagline", ""))  # 컨셉 브랜드 문구
    cta   = strip_hanja(cp.get("ctaCopy", "수강신청하기"))
    stats = cp.get("statBadges", [])
    
    # 💡 고정 키워드 제거! AI가 맥락에 맞게 생성한 'bannerTags'를 가져옵니다. (없으면 기본값)
    kws   = cp.get("bannerTags", SUBJ_KW.get(d["subject"], ["개념","기출","실전","파이널"]))
    
    bg_url= cp.get("bg_photo_url", "")
    hs    = T.get("heroStyle", "typographic")
    s     = _bg_vars(bg_url, T["dark"])
    dark  = T["dark"]

    kh = "".join(f'<span style="font-size:9px;font-weight:800;padding:5px 14px;border-radius:var(--r-btn,4px);color:{s["c1c"]};border:1px solid {s["bdc"]};margin:2px;letter-spacing:.1em">{k}</span>' for k in kws)
    sh = "".join(f'<div><div style="font-family:var(--fh);font-size:clamp(20px,3vw,30px);font-weight:900;color:{s["c1c"]}">{sv}</div><div style="font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.5);margin-top:2px">{sl}</div></div>' for sv,sl in stats) if stats else ""
    inst = f'<div style="display:inline-flex;align-items:center;gap:8px;margin-top:20px;padding:6px 16px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:var(--r-btn,4px)"><span style="font-size:11px;color:rgba(255,255,255,.75);font-weight:600">{d["name"]} 선생님</span></div>' if d["name"] and bg_url else ""

    # ── 레이아웃 1: TYPOGRAPHIC (기본) ────────────
    if hs == "typographic":
        deco_word = title[:3] if title else sub[:3]
        text_col = "#fff" if (dark or bg_url) else "var(--text)"
        t70_col  = "rgba(255,255,255,.7)" if (dark or bg_url) else "var(--t70)"
        accent_col = s["c1c"] if bg_url else "var(--c1)"
        return (
            f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:flex;flex-direction:column;justify-content:flex-end">'
            + s["overlay"]
            + f'<div style="position:absolute;top:0;left:0;right:0;bottom:0;background:linear-gradient(to top,rgba(0,0,0,.92) 0%,rgba(0,0,0,.25) 50%,transparent 100%);z-index:1;pointer-events:none"></div>'
            + f'<div style="position:absolute;top:-0.05em;right:-0.05em;font-family:\'Black Han Sans\',var(--fh);font-size:40vw;font-weight:900;line-height:0.85;color:var(--c1);opacity:.06;pointer-events:none;overflow:hidden;z-index:1;user-select:none">{deco_word}</div>'
            + f'<div style="position:relative;z-index:2;padding:clamp(60px,8vw,100px) clamp(40px,7vw,100px);max-width:min(1000px,100%)">'
            + f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:28px"><div style="width:36px;height:3px;background:{accent_col}"></div><span style="font-size:9.5px;font-weight:800;letter-spacing:.22em;text-transform:uppercase;color:{accent_col}">{sub}</span></div>'
            + f'<h1 style="font-family:\'Black Han Sans\',var(--fh);font-size:clamp(52px,8vw,140px);font-weight:900;line-height:.88;letter-spacing:-.03em;word-break:keep-all;overflow-wrap:break-word;color:{text_col};margin-bottom:20px" class="st">{title}</h1>'
            + (f'<div style="font-size:clamp(15px,1.7vw,20px);font-style:italic;font-weight:300;color:{accent_col};margin-bottom:18px;letter-spacing:-.01em;line-height:1.5;opacity:.9">{tagline}</div>' if tagline else "")
            + f'<div style="width:100%;height:1px;background:linear-gradient(to right,{accent_col},transparent);margin-bottom:24px;opacity:.4"></div>'
            + f'<p style="font-size:clamp(14px,1.6vw,17px);line-height:1.9;color:{t70_col};max-width:520px;padding-left:18px;border-left:3px solid {accent_col};margin-bottom:28px">{lead}</p>'
            + f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:28px">{kh}</div>'
            + inst
            + f'<div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:24px">'
            + f'<a class="btn-p" href="#" style="font-size:15px;padding:16px 40px">{cta} →</a>'
            + f'<a href="#" style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.08);{s["blur"] if bg_url else "backdrop-filter:blur(8px)"};color:{text_col};font-weight:600;padding:15px 28px;border-radius:var(--r-btn,4px);border:1.5px solid {"rgba(255,255,255,.3)" if (dark or bg_url) else "var(--bd)"};font-size:14px;text-decoration:none">강의 미리보기 ↗</a>'
            + (f'<div style="display:flex;gap:36px;margin-top:40px;padding-top:24px;border-top:1px solid {s["top_brd"]}">{sh}</div>' if sh else "")
            + '</div></div></section>'
        )

    # ── 레이아웃 2: CINEMATIC ──────────────────────
    elif hs == "cinematic":
        return (
            f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:flex;flex-direction:column;justify-content:flex-end">'
            + s["overlay"]
            + f'<div style="position:absolute;inset:0;background:linear-gradient(160deg,transparent 30%,rgba(0,0,0,.85) 100%);z-index:1;pointer-events:none"></div>'
            + f'<div style="position:absolute;top:0;left:0;right:0;height:6px;background:var(--c1);z-index:3"></div>'
            + f'<div style="position:absolute;bottom:0;left:0;right:0;height:6px;background:var(--c1);z-index:3"></div>'
            + f'<div style="position:relative;z-index:2;padding:80px clamp(40px,7vw,100px) 80px;display:grid;grid-template-columns:1fr 340px;gap:60px;align-items:flex-end">'
            + f'<div>'
            + f'<div style="display:inline-flex;align-items:center;gap:10px;margin-bottom:24px;padding:5px 18px;border:1.5px solid var(--c1);border-radius:var(--r-btn,2px)">'
            + f'<div style="width:8px;height:8px;background:var(--c1);border-radius:50%;animation:pulse-accent 1.5s ease-in-out infinite"></div>'
            + f'<span style="font-size:10px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:var(--c1)">{sub}</span></div>'
            + f'<h1 style="font-family:var(--fh);font-size:clamp(40px,6.5vw,96px);font-weight:900;line-height:.92;letter-spacing:-.04em;word-break:keep-all;overflow-wrap:break-word;color:#fff;margin-bottom:16px" class="st">{title}</h1>'
            + (f'<div style="font-size:clamp(14px,1.6vw,19px);font-style:italic;font-weight:300;color:var(--c1);margin-bottom:18px;line-height:1.5;opacity:.9">{tagline}</div>' if tagline else "")
            + f'<p style="font-size:15px;line-height:2;color:rgba(255,255,255,.72);max-width:480px;border-left:3px solid var(--c1);padding-left:20px;margin-bottom:32px">{lead}</p>'
            + f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:28px">{kh}</div>'
            + f'<div style="display:flex;gap:12px">'
            + f'<a class="btn-p" href="#" style="font-size:15px;padding:16px 44px;letter-spacing:.04em">{cta} →</a>'
            + f'<a href="#" style="display:inline-flex;align-items:center;gap:8px;color:rgba(255,255,255,.7);font-weight:600;padding:15px 24px;border-radius:var(--r-btn,2px);border:1.5px solid rgba(255,255,255,.25);font-size:14px;text-decoration:none">미리보기</a>'
            + f'</div>'
            + (f'<div style="display:flex;gap:40px;margin-top:44px;padding-top:22px;border-top:1px solid rgba(255,255,255,.15)">{sh}</div>' if sh else "")
            + f'</div>'
            + f'<div style="padding:28px;background:rgba(0,0,0,.7);{s["blur"]};border:1px solid rgba(255,255,255,.12);border-radius:var(--r,4px)">'
            + f'<div style="font-family:var(--fh);font-size:11px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:var(--c1);margin-bottom:16px">강의 정보</div>'
            + "".join(f'<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid rgba(255,255,255,.1)"><span style="font-size:11px;color:rgba(255,255,255,.5)">{l}</span><span style="font-size:12px;font-weight:700;color:#fff">{v}</span></div>' for l,v in [["강의 대상",d["target"]],["과목",d["subject"]],["브랜드",d["purpose_label"][:14]]])
            + f'<a class="btn-p" href="#" style="width:100%;justify-content:center;margin-top:18px;display:flex;font-size:13px">{cta} →</a>'
            + f'</div></div></section>'
        )

    # ── 레이아웃 3: BILLBOARD (초대형 타이포만) ─────
    elif hs == "billboard":
        bg_col = "var(--bg)"
        title_parts = title.split()
        line1 = title_parts[0] if title_parts else title
        line2 = " ".join(title_parts[1:]) if len(title_parts) > 1 else ""
        return (
            f'<section id="hero" style="min-height:100vh;background:{bg_col};position:relative;overflow:hidden;display:flex;flex-direction:column;justify-content:center;padding:80px clamp(40px,7vw,100px)">'
            + f'<div style="position:absolute;top:0;left:0;right:0;bottom:0;background:repeating-linear-gradient(0deg,transparent,transparent 79px,var(--bd) 79px,var(--bd) 80px);z-index:0;opacity:.3;pointer-events:none"></div>'
            + f'<div style="position:relative;z-index:1">'
            + f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:32px"><div style="width:48px;height:4px;background:var(--c1)"></div><span style="font-size:9.5px;font-weight:800;letter-spacing:.22em;text-transform:uppercase;color:var(--c1)">{sub}</span></div>'
            + f'<div style="font-family:var(--fh);font-size:clamp(56px,9vw,140px);font-weight:900;line-height:.88;letter-spacing:-.05em;word-break:keep-all;overflow-wrap:break-word;color:var(--text);margin-bottom:4px" class="st">{line1}</div>'
            + (f'<div style="font-family:var(--fh);font-size:clamp(56px,9vw,140px);font-weight:900;line-height:.88;letter-spacing:-.05em;word-break:keep-all;overflow-wrap:break-word;color:transparent;-webkit-text-stroke:2px var(--c1);">{line2}</div>' if line2 else "")
            + f'<div style="display:flex;align-items:center;gap:32px;margin-top:40px;padding-top:32px;border-top:2px solid var(--c1)">'
            + f'<p style="font-size:14px;line-height:1.9;color:var(--t70);max-width:380px">{lead}</p>'
            + (f'<div style="font-size:clamp(13px,1.5vw,18px);font-style:italic;font-weight:300;color:var(--c1);margin-top:12px;line-height:1.5">{tagline}</div>' if tagline else "")
            + f'<div style="display:flex;flex-direction:column;gap:10px;flex-shrink:0">'
            + f'<a class="btn-p" href="#" style="font-size:15px;padding:16px 44px">{cta} →</a>'
            + f'<div style="display:flex;gap:5px;flex-wrap:wrap">{kh}</div></div>'
            + f'</div>'
            + (f'<div style="display:flex;gap:36px;margin-top:40px;padding-top:24px;border-top:1px solid var(--bd)">{sh}</div>' if sh else "")
            + f'</div></section>'
        )

    # ── 레이아웃 4: EDITORIAL_BOLD ────────────────
    elif hs == "editorial_bold":
        text_col   = "#fff" if (dark or bg_url) else "var(--text)"
        t70_col    = "rgba(255,255,255,.75)" if (dark or bg_url) else "var(--t70)"
        accent_c   = s["c1c"] if bg_url else "var(--c1)"
        bd_c       = s["bdc"] if bg_url else "var(--bd)"
        return (
            f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:grid;grid-template-rows:auto 1fr auto">'
            + s["overlay"]
            + f'<div style="position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,.2) 0%,rgba(0,0,0,.75) 100%);z-index:1;pointer-events:none"></div>'
            + f'<div style="position:relative;z-index:2;padding:28px clamp(40px,6vw,88px);display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid {bd_c}">'
            + f'<div style="font-family:var(--fh);font-size:15px;font-weight:900;color:{text_col};letter-spacing:.06em">{d["subject"].upper()} · {d["name"] if d["name"] else "강사"}</div>'
            + f'<div style="display:flex;gap:5px">{kh}</div>'
            + f'</div>'
            + f'<div style="position:relative;z-index:2;padding:clamp(48px,6vw,80px) clamp(40px,6vw,88px);display:flex;flex-direction:column;justify-content:center">'
            + f'<div style="display:inline-flex;align-items:center;gap:8px;margin-bottom:20px"><span style="font-size:10px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:{accent_c}">{sub}</span></div>'
            + f'<h1 style="font-family:\'Black Han Sans\',var(--fh);font-size:clamp(40px,6vw,96px);font-weight:900;line-height:.9;letter-spacing:-.03em;word-break:keep-all;overflow-wrap:break-word;color:{text_col};max-width:800px;margin-bottom:16px" class="st">{title}</h1>'
            + (f'<div style="font-size:clamp(14px,1.5vw,18px);font-style:italic;font-weight:300;color:{accent_c};margin-bottom:20px;line-height:1.5;opacity:.9">{tagline}</div>' if tagline else "")
            + f'<div style="display:flex;gap:40px;align-items:flex-start;flex-wrap:wrap">'
            + f'<p style="font-size:clamp(13px,1.4vw,16px);line-height:1.95;color:{t70_col};max-width:420px;padding-left:20px;border-left:3px solid {accent_c}">{lead}</p>'
            + f'<div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0">'
            + f'<a class="btn-p" href="#" style="font-size:15px;padding:16px 44px">{cta} →</a>'
            + f'<a href="#" style="display:inline-flex;align-items:center;justify-content:center;gap:7px;color:{text_col};font-weight:600;padding:14px 24px;border-radius:var(--r-btn,4px);border:1.5px solid {bd_c};font-size:13px;text-decoration:none">강의 미리보기</a>'
            + f'</div></div></div>'
            + (f'<div style="position:relative;z-index:2;padding:24px clamp(40px,6vw,88px);border-top:1px solid {bd_c};display:flex;gap:48px">{sh}</div>' if sh else "<div></div>")
            + f'</section>'
        )

    # ── 레이아웃 5: SPLIT_BOLD ────────────────────
    elif hs == "split_bold":
        return (
            f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:grid;grid-template-columns:1fr 1fr">'
            + s["overlay"]
            + f'<div style="position:relative;z-index:2;display:flex;flex-direction:column;justify-content:center;padding:clamp(60px,7vw,100px) clamp(32px,5vw,64px)">'
            + f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:24px"><div style="width:40px;height:3px;background:{s["c1c"] if bg_url else "var(--c1)"}"></div><span style="font-size:9.5px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:{s["c1c"] if bg_url else "var(--c1)"}">{sub}</span></div>'
            + f'<h1 style="font-family:var(--fh);font-size:clamp(38px,5.5vw,72px);font-weight:900;line-height:.88;letter-spacing:-.04em;{"color:#fff" if (dark or bg_url) else "color:var(--text)"};margin-bottom:20px" class="st">{title}</h1>'
            + f'<p style="font-size:14px;line-height:2;{"color:rgba(255,255,255,.72)" if (dark or bg_url) else "color:var(--t70)"};max-width:380px;margin-bottom:28px">{lead}</p>'
            + f'<div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:24px">{kh}</div>'
            + f'<a class="btn-p" href="#" style="align-self:flex-start;font-size:14px;padding:14px 36px">{cta} →</a>'
            + f'</div>'
            + f'<div style="position:relative;z-index:2;background:var(--c1);display:flex;align-items:center;justify-content:center;padding:48px 36px">'
            + f'<div style="width:100%;max-width:320px">'
            + f'<div style="font-size:11px;font-weight:800;letter-spacing:.15em;text-transform:uppercase;color:rgba(0,0,0,.5);margin-bottom:20px">{d["purpose_label"]}</div>'
            + f'<div style="font-family:var(--fh);font-size:clamp(32px,3.5vw,48px);font-weight:900;color:#fff;line-height:1.05;margin-bottom:20px">{title}</div>'
            + "".join(f'<div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.2)"><span style="font-size:11px;color:rgba(255,255,255,.6)">{l}</span><span style="font-size:12px;font-weight:700;color:#fff">{v}</span></div>' for l,v in [["대상",d["target"]],["과목",d["subject"]]])
            + f'<a style="display:flex;align-items:center;justify-content:center;gap:8px;background:#fff;color:var(--c1);font-weight:800;font-size:14px;padding:14px;border-radius:var(--r-btn,4px);margin-top:20px;text-decoration:none">{cta} →</a>'
            + f'</div></div></section>'
        )

    # ── 레이아웃 6: IMMERSIVE / 기본 SPLIT ────────
    else:  # immersive or split
        return (
            f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:flex;flex-direction:column;justify-content:flex-end">'
            + s["overlay"]
            + f'<div style="position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.9) 0%,rgba(0,0,0,.1) 60%,transparent 100%);z-index:1;pointer-events:none"></div>'
            + f'<div style="position:relative;z-index:2;padding:clamp(48px,6vw,80px) clamp(36px,6vw,88px);max-width:900px">'
            + f'<div style="display:inline-flex;align-items:center;gap:9px;background:rgba(255,255,255,.12);{s["blur"]};padding:6px 18px;border-radius:100px;margin-bottom:22px;border:1px solid rgba(255,255,255,.2)">'
            + f'<span style="font-size:10px;font-weight:800;color:#fff;letter-spacing:.14em;text-transform:uppercase">{sub}</span></div>'
            + f'<h1 style="font-family:var(--fh);font-size:clamp(36px,5vw,80px);font-weight:900;line-height:.95;letter-spacing:-.04em;word-break:keep-all;overflow-wrap:break-word;color:#fff;margin-bottom:20px" class="st">{title}</h1>'
            + f'<p style="font-size:clamp(13px,1.5vw,16px);line-height:1.9;color:rgba(255,255,255,.78);max-width:500px;margin-bottom:28px;padding-left:18px;border-left:3px solid #fff">{lead}</p>'
            + f'<div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:28px">{kh}</div>'
            + inst
            + f'<div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:22px">'
            + f'<a class="btn-p" href="#" style="font-size:15px;padding:16px 44px">{cta} →</a>'
            + f'<a href="#" style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.1);{s["blur"]};color:#fff;font-weight:600;padding:15px 28px;border-radius:100px;border:1.5px solid rgba(255,255,255,.3);font-size:14px;text-decoration:none">강의 미리보기 ↗</a>'
            + f'</div>'
            + (f'<div style="display:flex;gap:36px;margin-top:44px;padding-top:24px;border-top:1px solid rgba(255,255,255,.18)">{sh}</div>' if sh else "")
            + f'</div></section>'
        )


def sec_intro(d, cp, T):
    ip   = st.session_state.get("inst_profile") or {}
    t    = strip_hanja(cp.get("introTitle", f"{d['name']} 선생님 소개" if d["name"] else f"{d['subject']} 강사 소개"))
    desc = strip_hanja(cp.get("introDesc", f"{d['subject']} 최상위권 합격의 비결"))
    bio  = strip_hanja(cp.get("introBio", ip.get("desc", f"검증된 {d['subject']} 강사")))
    methods = [strip_hanja(m) for m in (ip.get("signatureMethods") or []) if m and m not in ("없음","")]
    slogan  = strip_hanja(ip.get("slogan",""))
    mtags = "".join(
        f'<div style="display:flex;align-items:center;gap:10px;padding:12px 16px;border:1.5px solid var(--c1);border-radius:var(--r,4px);margin-bottom:8px">'
        f'<div style="width:6px;height:6px;border-radius:50%;background:var(--c1);flex-shrink:0"></div>'
        f'<span style="font-size:13px;font-weight:800;color:var(--text);letter-spacing:.04em">{m}</span>'
        f'</div>'
        for m in methods[:4]
    ) if methods else f'<div style="font-size:13px;color:var(--t45)">{d["subject"]} 전문 강의</div>'
    slogan_html = (
        f'<div class="rv d1" style="padding:28px 32px;background:var(--bg3);border-radius:var(--r,4px);position:relative;overflow:hidden;margin-top:24px">'
        f'<div style="position:absolute;top:-12px;left:12px;font-family:var(--fh);font-size:110px;font-weight:900;color:var(--c1);opacity:.06;line-height:1;pointer-events:none">\"</div>'
        f'<p style="font-size:clamp(14px,1.4vw,17px);line-height:1.9;font-style:italic;color:var(--text);font-weight:500;position:relative;z-index:1;padding-top:10px">{slogan}</p>'
        f'<div style="display:flex;align-items:center;gap:8px;margin-top:14px">'
        f'<div style="width:24px;height:2px;background:var(--c1)"></div>'
        f'<span style="font-size:10px;font-weight:800;color:var(--c1);letter-spacing:.12em;text-transform:uppercase">{d["name"] if d["name"] else "강사"} 선생님</span>'
        f'</div></div>'
    ) if slogan else ""
    return (
        f'<section class="sec alt" id="intro">'
        f'<div style="max-width:1200px;margin:0 auto">'
        # 상단 헤더 바
        f'<div class="rv" style="display:grid;grid-template-columns:1fr auto;align-items:flex-end;gap:24px;padding-bottom:28px;border-bottom:3px solid var(--c1);margin-bottom:52px">'
        f'<div>'
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">'
        f'<div style="width:40px;height:3px;background:var(--c1)"></div>'
        f'<span style="font-size:9.5px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:var(--c1)">강사 소개</span>'
        f'</div>'
        f'<h2 style="font-family:\'Black Han Sans\',var(--fh);font-size:clamp(28px,4vw,52px);font-weight:900;line-height:1.05;letter-spacing:-.02em;color:var(--text);margin:0">{t}</h2>'
        f'</div>'
        f'<div style="text-align:right">'
        f'<div style="font-size:10px;font-weight:800;letter-spacing:.14em;color:var(--t45);text-transform:uppercase;margin-bottom:6px">{d["subject"]}</div>'
        f'<div style="font-family:\'Black Han Sans\',var(--fh);font-size:22px;font-weight:900;color:var(--c1)">{d["purpose_label"][:14]}</div>'
        f'</div></div>'
        # 본문 3컬럼
        f'<div style="display:grid;grid-template-columns:1.3fr 1fr 0.85fr;gap:48px;align-items:start">'
        # 왼쪽: 설명 + 슬로건
        f'<div class="rv d1">'
        f'<p style="font-size:15px;line-height:2;color:var(--t70)">{desc}</p>'
        f'{slogan_html}'
        f'</div>'
        # 가운데: 프로필
        f'<div class="rv d2" style="padding:28px;background:var(--bg3);border-radius:var(--r,4px);border-left:3px solid var(--c1)">'
        f'<div style="font-size:9.5px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;color:var(--c1);margin-bottom:14px">PROFILE</div>'
        f'<p style="font-size:13.5px;line-height:2;color:var(--text)">{bio}</p>'
        f'</div>'
        # 오른쪽: 시그니처
        f'<div class="rv d3">'
        f'<div style="font-size:9.5px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;color:var(--c1);margin-bottom:16px">SIGNATURE</div>'
        f'{mtags}'
        f'</div>'
        f'</div>'
        f'</div></section>'
    )

def sec_why(d, cp, T):
    t = strip_hanja(cp.get('whyTitle', '이 강의가 필요한 이유'))
    s = strip_hanja(cp.get('whySub', f"{d['subject']} 1등급의 비결"))
    reasons = cp.get('whyReasons', [
        ['🎯','유형별 완전 정복','수능 출제 유형을 완전히 분석하여 어떤 문제도 흔들리지 않는 실력을 만듭니다.'],
        ['📊','기출 데이터 분석','최근 5년 기출을 철저히 분석하여 실전에서 반드시 나오는 유형만 집중 훈련합니다.'],
        ['⚡','실전 속도 훈련','정확도와 속도를 동시에 잡아 70분 안에 45문항을 완벽히 소화하는 훈련을 합니다.'],
    ])
    safe_r = []
    for it in reasons:
        if isinstance(it, (list, tuple)) and len(it) >= 3:
            safe_r.append((str(it[0]), str(it[1]), str(it[2])))
        elif isinstance(it, dict):
            safe_r.append((it.get('icon','✦'), it.get('title',''), it.get('desc','')))

    v = random.randint(0, 3)

    if v == 1:
        rh = ""
        for i,(ic,tt,dc) in enumerate(safe_r):
            rh += (
                f'<div class="card rv d{min(i+1,4)}" style="padding:32px 24px;text-align:center">'
                f'<div style="font-size:44px;margin-bottom:10px">{ic}</div>'
                f'<div style="font-family:var(--fh);font-size:52px;font-weight:900;color:var(--c1);opacity:.2;line-height:1;margin-bottom:10px">{i+1:02d}</div>'
                f'<div style="font-size:15px;font-weight:800;color:var(--text);margin-bottom:10px">{strip_hanja(tt)}</div>'
                f'<p style="font-size:13px;line-height:1.85;color:var(--t70);margin:0">{strip_hanja(dc)}</p>'
                f'</div>'
            )
        return (
            f'<section class="sec" id="why"><div style="max-width:1200px;margin:0 auto">'
            f'<div class="rv" style="text-align:center;margin-bottom:40px">'
            f'<div class="tag-line" style="justify-content:center">수강 이유</div>'
            f'<h2 class="sec-h2 st" style="text-align:center">{t}</h2>'
            f'<p class="sec-sub" style="text-align:center;margin:0 auto">{s}</p></div>'
            f'<div style="display:grid;grid-template-columns:repeat({min(len(safe_r),3)},1fr);gap:16px">{rh}</div>'
            f'</div></section>'
        )

    elif v == 2:
        rh = ""
        for i,(ic,tt,dc) in enumerate(safe_r):
            bg_color = "var(--bg2)" if i%2==0 else "var(--bg3)"
            rh += (
                f'<div class="rv d{min(i+1,4)}" style="display:grid;grid-template-columns:100px 1fr;'
                f'background:{bg_color};border-radius:var(--r,4px);overflow:hidden;margin-bottom:6px">'
                f'<div style="background:var(--c1);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px 12px">'
                f'<div style="font-size:28px">{ic}</div>'
                f'<div style="font-family:var(--fh);font-size:24px;font-weight:900;color:var(--on-c1, var(--bg));opacity:0.4;margin-top:4px">{i+1:02d}</div>'
                f'</div>'
                f'<div style="padding:24px 32px;display:flex;flex-direction:column;justify-content:center">'
                f'<div style="font-size:16px;font-weight:800;color:var(--text);margin-bottom:8px">{strip_hanja(tt)}</div>'
                f'<p style="font-size:13.5px;line-height:1.85;color:var(--t70);margin:0">{strip_hanja(dc)}</p>'
                f'</div></div>'
            )
        return (
            f'<section class="sec alt" id="why"><div style="max-width:1000px;margin:0 auto">'
            f'<div class="rv" style="margin-bottom:40px">'
            f'<div class="tag-line">수강 이유</div>'
            f'<h2 class="sec-h2 st">{t}</h2>'
            f'<p class="sec-sub">{s}</p></div>'
            f'{rh}</div></section>'
        )

    elif v == 3:
        rh = ""
        for i,(ic,tt,dc) in enumerate(safe_r):
            line_html = f'<div style="width:2px;flex:1;background:var(--bd);margin-top:8px;min-height:40px"></div>' if i < len(safe_r)-1 else ''
            rh += (
                f'<div class="rv d{min(i+1,4)}" style="display:grid;grid-template-columns:56px 1fr;gap:20px;margin-bottom:28px">'
                f'<div style="display:flex;flex-direction:column;align-items:center">'
                f'<div style="width:56px;height:56px;border-radius:50%;background:var(--c1);display:flex;align-items:center;justify-content:center;font-size:22px;color:var(--on-c1, var(--bg));flex-shrink:0">{ic}</div>'
                f'{line_html}'
                f'</div>'
                f'<div style="padding-top:12px">'
                f'<div style="font-size:16px;font-weight:800;color:var(--text);margin-bottom:8px">{strip_hanja(tt)}</div>'
                f'<p style="font-size:13.5px;line-height:1.85;color:var(--t70)">{strip_hanja(dc)}</p>'
                f'</div></div>'
            )
        return (
            f'<section class="sec" id="why"><div style="max-width:800px;margin:0 auto">'
            f'<div class="rv" style="margin-bottom:48px">'
            f'<div class="tag-line">수강 이유</div>'
            f'<h2 class="sec-h2 st">{t}</h2>'
            f'<p class="sec-sub">{s}</p></div>'
            f'{rh}</div></section>'
        )

    else:
        rh = ''
        for i,(ic,tt,dc) in enumerate(safe_r):
            alt_bg = 'background:var(--bg3)' if i%2==0 else 'background:var(--bg2)'
            rh += (
                f'<div class="rv d{min(i+1,4)}" style="display:grid;grid-template-columns:100px 1fr;'
                f'border:1px solid var(--bd);border-radius:var(--r,4px);margin-bottom:12px;overflow:visible">'
                f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;'
                f'{alt_bg};padding:20px 12px;border-right:1px solid var(--bd);border-radius:var(--r,4px) 0 0 var(--r,4px)">'
                f'<div style="font-family:var(--fh);font-size:36px;font-weight:900;color:var(--c1);opacity:.4">{i+1:02d}</div>'
                f'<div style="font-size:24px;margin-top:6px">{ic}</div>'
                f'</div>'
                f'<div style="padding:20px 24px">'
                f'<div style="font-size:clamp(14px,1.4vw,17px);font-weight:800;margin-bottom:8px;color:var(--text)">{strip_hanja(tt)}</div>'
                f'<p style="font-size:13px;line-height:1.85;color:var(--t70);margin:0">{strip_hanja(dc)}</p>'
                f'</div></div>'
            )
        return (
            f'<section class="sec" id="why">'
            f'<div style="display:grid;grid-template-columns:1fr 1.6fr;gap:60px;align-items:start;max-width:1200px;margin:0 auto">'
            f'<div class="rv" style="position:sticky;top:60px">'
            f'<div class="tag-line">수강 이유</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{s}</p>'
            f'<div style="padding:20px 24px;background:var(--c1);border-radius:var(--r,4px)">'
            f'<div style="font-family:var(--fh);font-size:48px;font-weight:900;color:var(--on-c1, var(--bg));line-height:1">{len(safe_r)}</div>'
            f'<div style="font-size:12px;color:var(--on-c1, var(--bg));opacity:0.8;margin-top:4px;font-weight:700">가지 핵심 이유</div>'
            f'</div></div>'
            f'<div class="rv d1">{rh}</div>'
            f'</div></section>'
        )

def sec_curriculum(d, cp, T):
    t = strip_hanja(cp.get("curriculumTitle", f"{d['purpose_label']} 커리큘럼"))
    s = strip_hanja(cp.get("curriculumSub", "단계별 완성 로드맵"))
    steps = cp.get("curriculumSteps", [
        ["01","개념 완성","핵심 개념을 정확히 이해하고 내 것으로 만드는 단계입니다.","4주"],
        ["02","유형 훈련","기출 완전 분석으로 실전 패턴 파악","4주"],
        ["03","심화 특훈","고난도 아이디어 체화","3주"],
        ["04","파이널","실전 완성","3주"],
    ])

    v = random.randint(0, 4)

    if v == 1:
        sh = ""
        for i, step in enumerate(steps):
            line_html = f'<div style="position:absolute;top:26px;left:calc(50% + 36px);right:calc(-50% + 36px);height:2px;background:var(--bd)"></div>' if i < len(steps)-1 else ''
            sh += (
                f'<div class="rv d{min(i+1,4)}" style="flex:1;min-width:160px;text-align:center;position:relative">'
                f'<div style="width:52px;height:52px;border-radius:50%;background:var(--c1);display:flex;align-items:center;justify-content:center;margin:0 auto 14px;font-family:var(--fh);font-size:15px;font-weight:900;color:var(--on-c1, var(--bg))">{str(step[0])}</div>'
                f'<div style="font-size:14px;font-weight:800;color:var(--text);margin-bottom:8px">{strip_hanja(str(step[1]))}</div>'
                f'<p style="font-size:12px;line-height:1.75;color:var(--t70)">{strip_hanja(str(step[2]))}</p>'
                f'<div style="font-size:9px;background:var(--bg3);color:var(--c1);padding:3px 10px;border-radius:100px;font-weight:700;display:inline-block;margin-top:8px;border:1px solid var(--bd)">{str(step[3]) if len(step)>3 else "4주"}</div>'
                f'{line_html}'
                f'</div>'
            )
        return (
            f'<section class="sec alt" id="curriculum"><div style="max-width:1200px;margin:0 auto">'
            f'<div class="rv" style="text-align:center;margin-bottom:52px">'
            f'<div class="tag-line" style="justify-content:center">커리큘럼</div>'
            f'<h2 class="sec-h2 st" style="text-align:center">{t}</h2>'
            f'<p class="sec-sub" style="text-align:center;margin:0 auto">{s}</p></div>'
            f'<div style="display:flex;gap:0;align-items:flex-start;flex-wrap:wrap">{sh}</div>'
            f'</div></section>'
        )

    elif v == 2:
        sh = ""
        for i, step in enumerate(steps):
            sh += (
                f'<div class="rv d{min(i+1,4)}" style="display:flex;gap:20px;align-items:flex-start;padding:20px 0;border-bottom:1px solid var(--bd)">'
                f'<div style="flex-shrink:0;width:40px;height:40px;border-radius:var(--r-btn,4px);background:var(--c1);display:flex;align-items:center;justify-content:center;font-size:16px;color:var(--on-c1, var(--bg));font-weight:900">✓</div>'
                f'<div style="flex:1">'
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
                f'<span style="font-size:15px;font-weight:800;color:var(--text)">{strip_hanja(str(step[1]))}</span>'
                f'<span style="font-size:9px;background:var(--bg3);color:var(--c1);padding:2px 10px;border-radius:100px;font-weight:700;border:1px solid var(--bd)">{str(step[3]) if len(step)>3 else "4주"}</span>'
                f'</div>'
                f'<p style="font-size:13px;line-height:1.8;color:var(--t70);margin:0">{strip_hanja(str(step[2]))}</p>'
                f'</div></div>'
            )
        return (
            f'<section class="sec" id="curriculum"><div style="max-width:900px;margin:0 auto">'
            f'<div class="rv" style="margin-bottom:40px">'
            f'<div class="tag-line">커리큘럼</div>'
            f'<h2 class="sec-h2 st">{t}</h2>'
            f'<p class="sec-sub">{s}</p></div>'
            f'{sh}</div></section>'
        )

    elif v == 3:
        sh = ""
        for i, step in enumerate(steps):
            sh += f'<div class="rv d{min(i+1,4)}" style="display:grid;grid-template-columns:1fr 64px 1fr;gap:0;align-items:center;margin-bottom:16px">'
            if i % 2 == 0:
                sh += (
                    f'<div style="padding:24px 28px;background:var(--bg3);border-radius:var(--r,4px) 0 0 var(--r,4px);border:1px solid var(--bd);border-right:none">'
                    f'<div style="font-size:15px;font-weight:800;color:var(--text);margin-bottom:8px">{strip_hanja(str(step[1]))}</div>'
                    f'<p style="font-size:13px;line-height:1.8;color:var(--t70);margin:0">{strip_hanja(str(step[2]))}</p></div>'
                    f'<div style="background:var(--c1);height:100%;display:flex;align-items:center;justify-content:center;font-family:var(--fh);font-size:14px;font-weight:900;color:var(--on-c1, var(--bg))">{str(step[0])}</div>'
                    f'<div style="padding:24px 28px;border-radius:0 var(--r,4px) var(--r,4px) 0;border:1px solid var(--bd);border-left:none">'
                    f'<span style="font-size:9px;background:var(--bg3);color:var(--c1);padding:3px 10px;border-radius:100px;font-weight:700;border:1px solid var(--bd)">{str(step[3]) if len(step)>3 else "4주"}</span>'
                    f'</div>'
                )
            else:
                sh += (
                    f'<div style="padding:24px 28px;border-radius:var(--r,4px) 0 0 var(--r,4px);border:1px solid var(--bd);border-right:none">'
                    f'<span style="font-size:9px;background:var(--bg3);color:var(--c1);padding:3px 10px;border-radius:100px;font-weight:700;border:1px solid var(--bd)">{str(step[3]) if len(step)>3 else "4주"}</span>'
                    f'</div>'
                    f'<div style="background:var(--c1);height:100%;display:flex;align-items:center;justify-content:center;font-family:var(--fh);font-size:14px;font-weight:900;color:var(--on-c1, var(--bg))">{str(step[0])}</div>'
                    f'<div style="padding:24px 28px;background:var(--bg3);border-radius:0 var(--r,4px) var(--r,4px) 0;border:1px solid var(--bd);border-left:none">'
                    f'<div style="font-size:15px;font-weight:800;color:var(--text);margin-bottom:8px">{strip_hanja(str(step[1]))}</div>'
                    f'<p style="font-size:13px;line-height:1.8;color:var(--t70);margin:0">{strip_hanja(str(step[2]))}</p></div>'
                )
            sh += f'</div>'
        return (
            f'<section class="sec alt" id="curriculum"><div style="max-width:1000px;margin:0 auto">'
            f'<div class="rv" style="text-align:center;margin-bottom:48px">'
            f'<div class="tag-line" style="justify-content:center">커리큘럼</div>'
            f'<h2 class="sec-h2 st" style="text-align:center">{t}</h2>'
            f'<p class="sec-sub" style="text-align:center;margin:0 auto">{s}</p></div>'
            f'{sh}</div></section>'
        )

    elif v == 4:
        STEP_COLORS = [
            ("var(--c1)", "var(--on-c1, var(--bg))"),
            ("var(--c2)", "var(--c4)"),
            ("var(--bg3)", "var(--text)"),
            ("var(--c3)", "var(--c4)"),
        ]
        sh = ""
        for idx, step in enumerate(steps):
            no   = str(step[0]); tt = str(step[1]); dc = str(step[2])
            du   = str(step[3]) if len(step) > 3 else "4주"
            bg_c, tx_c = STEP_COLORS[idx % len(STEP_COLORS)]
            num_block = (
                f'<div style="background:{bg_c};display:flex;flex-direction:column;align-items:center;justify-content:center;padding:32px;position:relative;overflow:hidden">'
                f'<div style="position:absolute;font-family:var(--fh);font-size:120px;font-weight:900;color:rgba(0,0,0,.08);line-height:1;top:50%;left:50%;transform:translate(-50%,-50%);pointer-events:none">{idx+1}</div>'
                f'<div style="font-family:var(--fh);font-size:64px;font-weight:900;color:{tx_c};line-height:1;position:relative;z-index:1">{idx+1}</div>'
                f'<div style="font-size:11px;font-weight:800;color:{tx_c};opacity:.6;letter-spacing:.12em;margin-top:4px;text-transform:uppercase;position:relative;z-index:1">STEP</div>'
                f'</div>'
            )
            content_block = (
                f'<div style="background:var(--bg3);padding:32px;border:1px solid var(--bd)">'
                f'<div style="font-size:10px;font-weight:800;color:var(--c1);letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px">{du}</div>'
                f'<div style="font-family:var(--fh);font-size:18px;font-weight:700;color:var(--text);margin-bottom:10px">{strip_hanja(tt)}</div>'
                f'<p style="font-size:13px;line-height:1.85;color:var(--t70);margin:0">{strip_hanja(dc)}</p></div>'
            )
            if idx % 2 == 0:
                sh += f'<div class="rv d{min(idx+1,4)}" style="display:grid;grid-template-columns:200px 1fr;min-height:200px;border-radius:var(--r,4px);overflow:hidden;margin-bottom:12px">{num_block}{content_block}</div>'
            else:
                sh += f'<div class="rv d{min(idx+1,4)}" style="display:grid;grid-template-columns:1fr 200px;min-height:200px;border-radius:var(--r,4px);overflow:hidden;margin-bottom:12px">{content_block}{num_block}</div>'
        
        return (
            f'<section class="sec" id="curriculum">'
            f'<div style="max-width:900px;margin:0 auto">'
            f'<div class="rv" style="text-align:center;margin-bottom:48px">'
            f'<div class="tag-line" style="justify-content:center">커리큘럼</div>'
            f'<h2 class="sec-h2 st" style="text-align:center">{t}</h2>'
            f'<p class="sec-sub" style="text-align:center;margin:0 auto">{s}</p></div>'
            f'{sh}</div></section>'
        )

    else:
        sh = ""
        for idx, step in enumerate(steps):
            no = str(step[0]); tt = str(step[1]); dc = str(step[2])
            du = str(step[3]) if len(step) > 3 else "4주"
            margin_b = "0" if idx == len(steps)-1 else "12px"
            bg_col_left = "var(--c1)" if idx%2==0 else "var(--bg3)"
            border_col_left = "var(--c1)" if idx%2==0 else "var(--bd)"
            text_col_step = "var(--on-c1, var(--bg))" if idx%2==0 else "var(--t45)"
            text_col_num = "var(--on-c1, var(--bg))" if idx%2==0 else "var(--c1)"
            opacity_step = "0.6" if idx%2==0 else "1"

            sh += (
                f'<div class="rv d{min(idx+1,4)}" style="display:flex;gap:0;align-items:stretch;margin-bottom:{margin_b}">'
                f'<div style="flex-shrink:0;width:72px;background:{bg_col_left};display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px 8px;border-radius:var(--r,4px) 0 0 var(--r,4px);border:1px solid {border_col_left};border-right:none">'
                f'<div style="font-family:\'Black Han Sans\',var(--fh);font-size:11px;font-weight:900;color:{text_col_step};opacity:{opacity_step};letter-spacing:.1em">STEP</div>'
                f'<div style="font-family:\'Black Han Sans\',var(--fh);font-size:26px;font-weight:900;color:{text_col_num};line-height:1;margin-top:2px">{idx+1:02d}</div>'
                f'</div>'
                f'<div style="flex:1;padding:22px 28px;background:var(--bg);border-radius:0 var(--r,4px) var(--r,4px) 0;border:1px solid var(--bd);border-left:none">'
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">'
                f'<div style="font-family:\'Black Han Sans\',var(--fh);font-size:16px;font-weight:900;color:var(--text)">{strip_hanja(tt)}</div>'
                f'<span style="font-size:9px;background:var(--bg3);color:var(--c1);padding:3px 12px;border-radius:100px;font-weight:800;border:1px solid var(--bd);flex-shrink:0">{du}</span>'
                f'</div>'
                f'<p style="font-size:13px;line-height:1.85;color:var(--t70);margin:0">{strip_hanja(dc)}</p>'
                f'</div></div>'
            )
        return (
            f'<section class="sec alt" id="curriculum">'
            f'<div style="display:grid;grid-template-columns:1fr 1.5fr;gap:72px;align-items:start;max-width:1200px;margin:0 auto">'
            f'<div class="rv" style="position:sticky;top:60px">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">'
            f'<div style="width:40px;height:3px;background:var(--c1)"></div>'
            f'<span style="font-size:9.5px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:var(--c1)">커리큘럼</span>'
            f'</div>'
            f'<h2 style="font-family:\'Black Han Sans\',var(--fh);font-size:clamp(26px,3.5vw,44px);font-weight:900;line-height:1.05;color:var(--text);margin-bottom:12px">{t}</h2>'
            f'<p style="font-size:14px;line-height:1.9;color:var(--t70);margin-bottom:32px">{s}</p>'
            f'<div style="padding:24px 28px;background:var(--c1);border-radius:var(--r,4px)">'
            f'<div style="font-size:9.5px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--on-c1, var(--bg));opacity:0.6;margin-bottom:10px">TOTAL</div>'
            f'<div style="font-family:\'Black Han Sans\',var(--fh);font-size:48px;font-weight:900;color:var(--on-c1, var(--bg));line-height:1">{len(steps)*4}주</div>'
            f'<div style="font-size:12px;color:var(--on-c1, var(--bg));opacity:.8;margin-top:6px;font-weight:600">{len(steps)}단계 완성 과정</div>'
            f'</div></div>'
            f'<div>{sh}</div>'
            f'</div></section>'
        )

def sec_curriculum(d, cp, T):
    t = strip_hanja(cp.get("curriculumTitle", f"{d['purpose_label']} 커리큘럼"))
    s = strip_hanja(cp.get("curriculumSub", "단계별 완성 로드맵"))
    steps = cp.get("curriculumSteps", [
        ["01","개념 완성","핵심 개념을 정확히 이해하고 내 것으로 만드는 단계입니다.","4주"],
        ["02","유형 훈련","기출 완전 분석으로 실전 패턴 파악","4주"],
        ["03","심화 특훈","고난도 아이디어 체화","3주"],
        ["04","파이널","실전 완성","3주"],
    ])

    v = random.randint(0, 4)

    if v == 1:
        sh = "".join(
            f'<div class="rv d{min(i+1,4)}" style="flex:1;min-width:160px;text-align:center;position:relative">'
            f'<div style="width:52px;height:52px;border-radius:50%;background:var(--c1);'
            f'display:flex;align-items:center;justify-content:center;margin:0 auto 14px;'
            f'font-family:var(--fh);font-size:15px;font-weight:900;color:var(--on-c1, var(--bg))">{str(step[0])}</div>'
            f'<div style="font-size:14px;font-weight:800;color:var(--text);margin-bottom:8px">{strip_hanja(str(step[1]))}</div>'
            f'<p style="font-size:12px;line-height:1.75;color:var(--t70)">{strip_hanja(str(step[2]))}</p>'
            f'<div style="font-size:9px;background:var(--bg3);color:var(--c1);padding:3px 10px;'
            f'border-radius:100px;font-weight:700;display:inline-block;margin-top:8px;border:1px solid var(--bd)">'
            f'{str(step[3]) if len(step)>3 else "4주"}</div>'
            + (f'<div style="position:absolute;top:26px;left:calc(50% + 36px);right:calc(-50% + 36px);'
               f'height:2px;background:var(--bd)"></div>' if i < len(steps)-1 else '')
            + f'</div>'
            for i, step in enumerate(steps)
        )
        return (
            f'<section class="sec alt" id="curriculum"><div style="max-width:1200px;margin:0 auto">'
            f'<div class="rv" style="text-align:center;margin-bottom:52px">'
            f'<div class="tag-line" style="justify-content:center">커리큘럼</div>'
            f'<h2 class="sec-h2 st" style="text-align:center">{t}</h2>'
            f'<p class="sec-sub" style="text-align:center;margin:0 auto">{s}</p></div>'
            f'<div style="display:flex;gap:0;align-items:flex-start;flex-wrap:wrap">{sh}</div>'
            f'</div></section>'
        )

    elif v == 2:
        sh = "".join(
            f'<div class="rv d{min(i+1,4)}" style="display:flex;gap:20px;align-items:flex-start;'
            f'padding:20px 0;border-bottom:1px solid var(--bd)">'
            f'<div style="flex-shrink:0;width:40px;height:40px;border-radius:var(--r-btn,4px);'
            f'background:var(--c1);display:flex;align-items:center;justify-content:center;'
            f'font-size:16px;color:var(--on-c1, var(--bg));font-weight:900">✓</div>'
            f'<div style="flex:1">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
            f'<span style="font-size:15px;font-weight:800;color:var(--text)">{strip_hanja(str(step[1]))}</span>'
            f'<span style="font-size:9px;background:var(--bg3);color:var(--c1);padding:2px 10px;'
            f'border-radius:100px;font-weight:700;border:1px solid var(--bd)">{str(step[3]) if len(step)>3 else "4주"}</span>'
            f'</div>'
            f'<p style="font-size:13px;line-height:1.8;color:var(--t70);margin:0">{strip_hanja(str(step[2]))}</p>'
            f'</div></div>'
            for i, step in enumerate(steps)
        )
        return (
            f'<section class="sec" id="curriculum"><div style="max-width:900px;margin:0 auto">'
            f'<div class="rv" style="margin-bottom:40px">'
            f'<div class="tag-line">커리큘럼</div>'
            f'<h2 class="sec-h2 st">{t}</h2>'
            f'<p class="sec-sub">{s}</p></div>'
            f'{sh}</div></section>'
        )

    elif v == 3:
        sh = "".join(
            f'<div class="rv d{min(i+1,4)}" style="display:grid;grid-template-columns:1fr 64px 1fr;'
            f'gap:0;align-items:center;margin-bottom:16px">'
            + (
                f'<div style="padding:24px 28px;background:var(--bg3);border-radius:var(--r,4px) 0 0 var(--r,4px);border:1px solid var(--bd);border-right:none">'
                f'<div style="font-size:15px;font-weight:800;color:var(--text);margin-bottom:8px">{strip_hanja(str(step[1]))}</div>'
                f'<p style="font-size:13px;line-height:1.8;color:var(--t70);margin:0">{strip_hanja(str(step[2]))}</p></div>'
                f'<div style="background:var(--c1);height:100%;display:flex;align-items:center;justify-content:center;'
                f'font-family:var(--fh);font-size:14px;font-weight:900;color:var(--on-c1, var(--bg))">{str(step[0])}</div>'
                f'<div style="padding:24px 28px;border-radius:0 var(--r,4px) var(--r,4px) 0;border:1px solid var(--bd);border-left:none">'
                f'<span style="font-size:9px;background:var(--bg3);color:var(--c1);padding:3px 10px;border-radius:100px;font-weight:700;border:1px solid var(--bd)">{str(step[3]) if len(step)>3 else "4주"}</span>'
                f'</div>'
                if i % 2 == 0 else
                f'<div style="padding:24px 28px;border-radius:var(--r,4px) 0 0 var(--r,4px);border:1px solid var(--bd);border-right:none">'
                f'<span style="font-size:9px;background:var(--bg3);color:var(--c1);padding:3px 10px;border-radius:100px;font-weight:700;border:1px solid var(--bd)">{str(step[3]) if len(step)>3 else "4주"}</span>'
                f'</div>'
                f'<div style="background:var(--c1);height:100%;display:flex;align-items:center;justify-content:center;'
                f'font-family:var(--fh);font-size:14px;font-weight:900;color:var(--on-c1, var(--bg))">{str(step[0])}</div>'
                f'<div style="padding:24px 28px;background:var(--bg3);border-radius:0 var(--r,4px) var(--r,4px) 0;border:1px solid var(--bd);border-left:none">'
                f'<div style="font-size:15px;font-weight:800;color:var(--text);margin-bottom:8px">{strip_hanja(str(step[1]))}</div>'
                f'<p style="font-size:13px;line-height:1.8;color:var(--t70);margin:0">{strip_hanja(str(step[2]))}</p></div>'
            )
            + f'</div>'
            for i, step in enumerate(steps)
        )
        return (
            f'<section class="sec alt" id="curriculum"><div style="max-width:1000px;margin:0 auto">'
            f'<div class="rv" style="text-align:center;margin-bottom:48px">'
            f'<div class="tag-line" style="justify-content:center">커리큘럼</div>'
            f'<h2 class="sec-h2 st" style="text-align:center">{t}</h2>'
            f'<p class="sec-sub" style="text-align:center;margin:0 auto">{s}</p></div>'
            f'{sh}</div></section>'
        )

    elif v == 4:
        STEP_COLORS = [
            ("var(--c1)", "var(--on-c1, var(--bg))"),
            ("var(--c2)", "var(--c4)"),
            ("var(--bg3)", "var(--text)"),
            ("var(--c3)", "var(--c4)"),
        ]
        sh = ""
        for idx, step in enumerate(steps):
            no   = str(step[0]); tt = str(step[1]); dc = str(step[2])
            du   = str(step[3]) if len(step) > 3 else "4주"
            bg_c, tx_c = STEP_COLORS[idx % len(STEP_COLORS)]
            is_left = idx % 2 == 0
            num_block = (
                f'<div style="background:{bg_c};display:flex;flex-direction:column;'
                f'align-items:center;justify-content:center;padding:32px;position:relative;overflow:hidden">'
                f'<div style="position:absolute;font-family:var(--fh);font-size:120px;font-weight:900;'
                f'color:rgba(0,0,0,.08);line-height:1;top:50%;left:50%;transform:translate(-50%,-50%);'
                f'pointer-events:none">{idx+1}</div>'
                f'<div style="font-family:var(--fh);font-size:64px;font-weight:900;'
                f'color:{tx_c};line-height:1;position:relative;z-index:1">{idx+1}</div>'
                f'<div style="font-size:11px;font-weight:800;color:{tx_c};opacity:.6;'
                f'letter-spacing:.12em;margin-top:4px;text-transform:uppercase;position:relative;z-index:1">STEP</div>'
                f'</div>'
            )
            content_block = (
                f'<div style="background:var(--bg3);padding:32px;border:1px solid var(--bd)">'
                f'<div style="font-size:10px;font-weight:800;color:var(--c1);letter-spacing:.12em;'
                f'text-transform:uppercase;margin-bottom:8px">{du}</div>'
                f'<div style="font-family:var(--fh);font-size:18px;font-weight:700;'
                f'color:var(--text);margin-bottom:10px">{strip_hanja(tt)}</div>'
                f'<p style="font-size:13px;line-height:1.85;color:var(--t70);margin:0">'
                f'{strip_hanja(dc)}</p></div>'
            )
            if is_left:
                sh += (
                    f'<div class="rv d{min(idx+1,4)}" style="display:grid;grid-template-columns:200px 1fr;'
                    f'min-height:200px;border-radius:var(--r,4px);overflow:hidden;margin-bottom:12px">'
                    + num_block + content_block + f'</div>'
                )
            else:
                sh += (
                    f'<div class="rv d{min(idx+1,4)}" style="display:grid;grid-template-columns:1fr 200px;'
                    f'min-height:200px;border-radius:var(--r,4px);overflow:hidden;margin-bottom:12px">'
                    + content_block + num_block + f'</div>'
                )
        return (
            f'<section class="sec" id="curriculum">'
            f'<div style="max-width:900px;margin:0 auto">'
            f'<div class="rv" style="text-align:center;margin-bottom:48px">'
            f'<div class="tag-line" style="justify-content:center">커리큘럼</div>'
            f'<h2 class="sec-h2 st" style="text-align:center">{t}</h2>'
            f'<p class="sec-sub" style="text-align:center;margin:0 auto">{s}</p></div>'
            f'{sh}</div></section>'
        )

    else:
        sh = ""
        for idx, step in enumerate(steps):
            no = str(step[0]); tt = str(step[1]); dc = str(step[2])
            du = str(step[3]) if len(step) > 3 else "4주"
            is_last = idx == len(steps)-1
            sh += (
                f'<div class="rv d{min(idx+1,4)}" style="display:flex;gap:0;align-items:stretch;'
                f'margin-bottom:{"0" if is_last else "12px"}">'
                f'<div style="flex-shrink:0;width:72px;background:{"var(--c1)" if idx%2==0 else "var(--bg3)"};'
                f'display:flex;flex-direction:column;align-items:center;justify-content:center;'
                f'padding:20px 8px;border-radius:var(--r,4px) 0 0 var(--r,4px);'
                f'border:1px solid {"var(--c1)" if idx%2==0 else "var(--bd)"};border-right:none">'
                f'<div style="font-family:\'Black Han Sans\',var(--fh);font-size:11px;font-weight:900;'
                f'color:{"var(--on-c1, var(--bg))" if idx%2==0 else "var(--t45)"}; opacity:{"0.6" if idx%2==0 else "1"}; letter-spacing:.1em">STEP</div>'
                f'<div style="font-family:\'Black Han Sans\',var(--fh);font-size:26px;font-weight:900;'
                f'color:{"var(--on-c1, var(--bg))" if idx%2==0 else "var(--c1)"};line-height:1;margin-top:2px">{idx+1:02d}</div>'
                f'</div>'
                f'<div style="flex:1;padding:22px 28px;background:var(--bg);'
                f'border-radius:0 var(--r,4px) var(--r,4px) 0;border:1px solid var(--bd);border-left:none">'
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">'
                f'<div style="font-family:\'Black Han Sans\',var(--fh);font-size:16px;font-weight:900;color:var(--text)">{strip_hanja(tt)}</div>'
                f'<span style="font-size:9px;background:var(--bg3);color:var(--c1);padding:3px 12px;'
                f'border-radius:100px;font-weight:800;border:1px solid var(--bd);flex-shrink:0">{du}</span>'
                f'</div>'
                f'<p style="font-size:13px;line-height:1.85;color:var(--t70);margin:0">{strip_hanja(dc)}</p>'
                f'</div></div>'
            )
        return (
            f'<section class="sec alt" id="curriculum">'
            f'<div style="display:grid;grid-template-columns:1fr 1.5fr;gap:72px;align-items:start;max-width:1200px;margin:0 auto">'
            f'<div class="rv" style="position:sticky;top:60px">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px">'
            f'<div style="width:40px;height:3px;background:var(--c1)"></div>'
            f'<span style="font-size:9.5px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:var(--c1)">커리큘럼</span>'
            f'</div>'
            f'<h2 style="font-family:\'Black Han Sans\',var(--fh);font-size:clamp(26px,3.5vw,44px);font-weight:900;line-height:1.05;color:var(--text);margin-bottom:12px">{t}</h2>'
            f'<p style="font-size:14px;line-height:1.9;color:var(--t70);margin-bottom:32px">{s}</p>'
            f'<div style="padding:24px 28px;background:var(--c1);border-radius:var(--r,4px)">'
            f'<div style="font-size:9.5px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--on-c1, var(--bg));opacity:0.6;margin-bottom:10px">TOTAL</div>'
            f'<div style="font-family:\'Black Han Sans\',var(--fh);font-size:48px;font-weight:900;color:var(--on-c1, var(--bg));line-height:1">{len(steps)*4}주</div>'
            f'<div style="font-size:12px;color:var(--on-c1, var(--bg));opacity:.8;margin-top:6px;font-weight:600">{len(steps)}단계 완성 과정</div>'
            f'</div></div>'
            f'<div>{sh}</div>'
            f'</div></section>'
        )


def sec_target(d, cp, T):
    t = strip_hanja(cp.get("targetTitle","이런 분들께 추천합니다"))
    items = [strip_hanja(str(it)) for it in cp.get("targetItems",[
        f"수능까지 {d['subject']} 점수를 확실히 올리고 싶은 분",
        "개념은 아는데 실전에서 점수가 안 나오는 분",
        "N수를 준비하며 체계적인 커리큘럼이 필요한 분",
        f"{d['subject']} 상위권 도약을 원하는 분",
    ])]
 
    v = random.randint(0, 3)
 
    if v == 1:
        # 체크마크 리스트
        ih = "".join(
            f'<div class="rv d{min(i+1,4)}" style="display:flex;gap:16px;align-items:flex-start;'
            f'padding:16px 0;border-bottom:1px solid var(--bd)">'
            f'<div style="flex-shrink:0;width:28px;height:28px;border-radius:50%;background:var(--c1);'
            f'display:flex;align-items:center;justify-content:center;font-size:13px;color:#fff;font-weight:900">✓</div>'
            f'<p style="font-size:15px;line-height:1.7;color:var(--text);font-weight:600;margin:0">{txt}</p>'
            f'</div>'
            for i,txt in enumerate(items)
        )
        return (
            f'<section class="sec" id="target"><div style="max-width:800px;margin:0 auto">'
            f'<div class="rv" style="text-align:center;margin-bottom:40px">'
            f'<div class="tag-line" style="justify-content:center">수강 대상</div>'
            f'<h2 class="sec-h2 st" style="text-align:center">{t}</h2></div>'
            f'{ih}</div></section>'
        )
 
    elif v == 2:
        # 큰 번호 강조
        ih = "".join(
            f'<div class="rv d{min(i+1,4)}" style="display:grid;grid-template-columns:80px 1fr;'
            f'gap:20px;align-items:center;padding:20px 0;border-bottom:1px solid var(--bd)">'
            f'<div style="font-family:var(--fh);font-size:clamp(44px,5vw,64px);font-weight:900;'
            f'color:var(--c1);opacity:.3;line-height:1;text-align:center">{i+1:02d}</div>'
            f'<p style="font-size:15px;line-height:1.75;color:var(--text);font-weight:600;margin:0">{txt}</p>'
            f'</div>'
            for i,txt in enumerate(items)
        )
        return (
            f'<section class="sec alt" id="target"><div style="max-width:900px;margin:0 auto">'
            f'<div class="rv" style="margin-bottom:40px">'
            f'<div class="tag-line">수강 대상</div><h2 class="sec-h2 st">{t}</h2></div>'
            f'{ih}</div></section>'
        )
 
    elif v == 3:
        # 페르소나 카드
        emojis = ["📚","✏️","🎯","💪"]
        grades = ["고3","N수생","고2","재학생"]
        ih = "".join(
            f'<div class="card rv d{min(i+1,4)}" style="padding:28px;text-align:center">'
            f'<div style="font-size:40px;margin-bottom:12px">{emojis[i%len(emojis)]}</div>'
            f'<div style="display:inline-block;background:var(--c1);color:#fff;font-size:10px;'
            f'font-weight:800;padding:3px 12px;border-radius:var(--r-btn,100px);margin-bottom:14px">{grades[i%len(grades)]}</div>'
            f'<p style="font-size:13.5px;line-height:1.75;color:var(--text);font-weight:600;margin:0">{txt}</p>'
            f'</div>'
            for i,txt in enumerate(items)
        )
        return (
            f'<section class="sec" id="target"><div style="max-width:1200px;margin:0 auto">'
            f'<div class="rv" style="text-align:center;margin-bottom:40px">'
            f'<div class="tag-line" style="justify-content:center">수강 대상</div>'
            f'<h2 class="sec-h2 st" style="text-align:center">{t}</h2></div>'
            f'<div style="display:grid;grid-template-columns:repeat({min(len(items),2)},1fr);gap:16px">{ih}</div>'
            f'</div></section>'
        )
 
    else:
        # 기존 엇갈린 카드
        left_items  = [(i,txt) for i,txt in enumerate(items) if i%2==0]
        right_items = [(i,txt) for i,txt in enumerate(items) if i%2==1]
        def card(i,txt):
            return (
                f'<div class="rv d{min(i+1,4)}" style="padding:22px 26px;border:1px solid var(--bd);'
                f'border-radius:var(--r,4px);background:var(--bg);margin-bottom:12px;'
                f'display:flex;gap:16px;align-items:flex-start">'
                f'<div style="flex-shrink:0;width:36px;height:36px;border-radius:var(--r-btn,4px);'
                f'background:var(--c1);display:flex;align-items:center;justify-content:center;'
                f'font-family:var(--fh);font-size:14px;font-weight:900;color:#fff">{i+1:02d}</div>'
                f'<p style="font-size:14px;font-weight:600;line-height:1.7;color:var(--text);margin:0">{txt}</p>'
                f'</div>'
            )
        lh = "".join(card(i,t2) for i,t2 in left_items)
        rh = "".join(card(i,t2) for i,t2 in right_items)
        return (
            f'<section class="sec" id="target"><div style="max-width:1200px;margin:0 auto">'
            f'<div class="rv" style="display:grid;grid-template-columns:1fr 2fr;gap:60px;align-items:start">'
            f'<div style="position:sticky;top:60px"><div class="tag-line">수강 대상</div>'
            f'<h2 class="sec-h2 st">{t}</h2></div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:0 20px">'
            f'<div>{lh}</div><div style="margin-top:56px">{rh}</div>'
            f'</div></div></div></section>'
        )

def sec_reviews(d, cp, T):
    reviews = cp.get("reviews", [
        [f'"개념이 이렇게 명확하게 보인 적이 없었어요. {d["subject"]} 공부가 달라졌습니다."', "고3 김OO","등급 향상"],
        ['"3주 만에 독해 속도가 확실히 빨라졌어요. 실전에서 시간이 남는 게 느껴졌습니다."', "N수 이OO","실전 완성"],
        [f'"선생님 덕분에 {d["subject"]} 구조가 보이기 시작했어요."', "고2 박OO","자신감 회복"],
    ])
    reviews = []
    for r in cp.get("reviews", []):
        if isinstance(r, dict):
            txt   = strip_hanja(str(r.get("quote", r.get("text", r.get("content", str(r))))))
            nm    = strip_hanja(str(r.get("name",  r.get("author", "수강생"))))
            badge = strip_hanja(str(r.get("badge", r.get("tag", "수강 완료"))))
            reviews.append([txt, nm, badge])
        elif isinstance(r, (list, tuple)):
            row = list(r) + ["", ""]
            reviews.append([strip_hanja(str(row[0])), strip_hanja(str(row[1])), strip_hanja(str(row[2]))])
        else:
            reviews.append([strip_hanja(str(r)), "수강생", "수강 완료"])
    if not reviews:
        reviews = [
            [f"{d['subject']} 공부 방식이 완전히 달라졌어요. 이제 지문이 보입니다.", "고3 김OO", "등급 향상"],
            ["막막했던 실전이 이제는 자신 있어요. 시간도 남아요.", "N수 이OO", "실전 완성"],
            [f"{d['subject']} 구조가 보이기 시작했어요. 선생님 덕분입니다.", "고2 박OO", "자신감 회복"],
        ]




## 문제 2 — AI 문구 품질 + 수강평 스키마 강화

 
    if not reviews:
        reviews = [
            [f"{d['subject']} 공부 방식이 완전히 달라졌어요. 이제 지문이 보입니다.", "고3 김OO", "등급 향상"],
            ["막막했던 실전이 이제는 자신 있어요. 시간도 남아요.", "N수 이OO", "실전 완성"],
            [f"{d['subject']} 구조가 보이기 시작했어요. 선생님 덕분입니다.", "고2 박OO", "자신감 회복"],
        ]

    import hashlib
    v = int(hashlib.md5((d.get("name","") + d.get("subject","") + str(len(reviews))).encode()).hexdigest(), 16) % 4
 
    if v == 1:
        # SNS 카드 스타일
        rh = "".join(
            f'<div class="card rv d{min(i+1,4)}" style="padding:24px">'
            f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">'
            f'<div style="width:40px;height:40px;border-radius:50%;background:var(--c1);'
            f'display:flex;align-items:center;justify-content:center;font-family:var(--fh);'
            f'font-size:16px;font-weight:900;color:#fff;flex-shrink:0">{nm[0] if nm else "익"}</div>'
            f'<div><div style="font-size:13px;font-weight:800;color:var(--text)">{nm}</div>'
            f'<div style="font-size:10px;color:var(--t45)">수강생</div></div>'
            f'<div style="margin-left:auto;font-size:10px;background:var(--bg3);color:var(--c1);'
            f'padding:3px 10px;border-radius:100px;font-weight:700;border:1px solid var(--bd)">{badge}</div>'
            f'</div>'
            f'<div style="display:flex;gap:2px;color:#F59E0B;font-size:12px;margin-bottom:12px">{"★"*5}</div>'
            f'<p style="font-size:13.5px;line-height:1.9;color:var(--text);font-weight:500">{strip_hanja(txt)}</p>'
            f'</div>'
            for i,(txt,nm,badge) in enumerate(reviews)
        )
        return (
            f'<section class="sec alt" id="reviews"><div style="max-width:1200px;margin:0 auto">'
            f'<div class="rv" style="margin-bottom:40px">'
            f'<div class="tag-line">수강평</div><h2 class="sec-h2 st">생생한 수강생 후기</h2></div>'
            f'<div style="display:grid;grid-template-columns:repeat({min(len(reviews),3)},1fr);gap:14px">{rh}</div>'
            f'</div></section>'
        )
 
    elif v == 2:
        # 큰 인용부호 강조
        rh = "".join(
            f'<div class="rv d{min(i+1,4)}" style="padding:40px;background:{"var(--bg2)" if i%2==0 else "var(--bg3)"};'
            f'border-radius:var(--r,4px);position:relative;overflow:hidden;margin-bottom:12px">'
            f'<div style="position:absolute;top:-20px;left:16px;font-family:var(--fh);font-size:140px;'
            f'font-weight:900;color:var(--c1);opacity:.06;line-height:1;pointer-events:none">"</div>'
            f'<p style="font-size:clamp(15px,1.5vw,18px);line-height:1.9;font-style:italic;'
            f'color:var(--text);font-weight:600;position:relative;z-index:1">{strip_hanja(txt)}</p>'
            f'<div style="display:flex;align-items:center;justify-content:space-between;margin-top:20px;'
            f'padding-top:16px;border-top:1px solid var(--bd)">'
            f'<div style="display:flex;gap:2px;color:#F59E0B;font-size:12px">{"★"*5}</div>'
            f'<div style="display:flex;align-items:center;gap:10px">'
            f'<span style="font-size:12px;color:var(--t45)">— {nm}</span>'
            f'<span style="font-size:10px;background:var(--c1);color:#fff;padding:3px 12px;'
            f'border-radius:100px;font-weight:700">{badge}</span>'
            f'</div></div></div>'
            for i,(txt,nm,badge) in enumerate(reviews)
        )
        return (
            f'<section class="sec" id="reviews"><div style="max-width:800px;margin:0 auto">'
            f'<div class="rv" style="text-align:center;margin-bottom:40px">'
            f'<div class="tag-line" style="justify-content:center">수강평</div>'
            f'<h2 class="sec-h2 st" style="text-align:center">생생한 수강생 후기</h2></div>'
            f'{rh}</div></section>'
        )
 
    elif v == 3:
        # 점수 강조 카드
        rh = "".join(
            f'<div class="card rv d{min(i+1,4)}" style="padding:28px">'
            f'<div style="display:flex;gap:3px;color:#F59E0B;font-size:14px;margin-bottom:14px">{"★"*5}</div>'
            f'<p style="font-size:14px;line-height:1.9;color:var(--text);font-weight:500;flex:1;margin-bottom:20px">{strip_hanja(txt)}</p>'
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'padding:14px 16px;background:var(--bg3);border-radius:var(--r,4px)">'
            f'<div style="font-family:var(--fh);font-size:22px;font-weight:900;color:var(--c1)">{badge}</div>'
            f'<div style="font-size:11px;color:var(--t45)">— {nm} 학생</div>'
            f'</div></div>'
            for i,(txt,nm,badge) in enumerate(reviews)
        )
        return (
            f'<section class="sec alt" id="reviews"><div style="max-width:1200px;margin:0 auto">'
            f'<div class="rv" style="margin-bottom:40px">'
            f'<div class="tag-line">수강평</div><h2 class="sec-h2 st">생생한 수강생 후기</h2></div>'
            f'<div style="display:grid;grid-template-columns:repeat({min(len(reviews),3)},1fr);gap:14px">{rh}</div>'
            f'</div></section>'
        )
 
    else:
        # 기존 스타일 (첫 카드 풀와이드 강조)
        rh = ""
        for i,(txt,nm,badge) in enumerate(reviews):
            if i == 0:
                rh += (
                    f'<div class="rv d1" style="grid-column:1 / -1;display:grid;grid-template-columns:1fr 1fr;gap:0;overflow:hidden;border-radius:var(--r,4px);border:2px solid var(--c1);box-shadow:0 0 40px rgba(0,0,0,.3)">'
                    f'<div style="background:var(--c1);padding:48px 40px;display:flex;flex-direction:column;justify-content:space-between;position:relative;overflow:hidden">'
                    f'<div style="position:absolute;top:-30px;left:-10px;font-family:\'Black Han Sans\',var(--fh);font-size:180px;font-weight:900;color:rgba(0,0,0,.12);line-height:1;pointer-events:none">"</div>'
                    f'<div style="position:relative;z-index:1">'
                    f'<div style="display:flex;gap:3px;color:#fff;font-size:20px;margin-bottom:20px;opacity:.7">{"★"*5}</div>'
                    f'<p style="font-size:clamp(16px,1.6vw,20px);line-height:1.85;font-weight:700;color:#fff">{strip_hanja(txt)}</p>'
                    f'</div>'
                    f'<div style="display:flex;align-items:center;justify-content:space-between;margin-top:28px;padding-top:20px;border-top:1px solid rgba(255,255,255,.25);position:relative;z-index:1">'
                    f'<span style="font-size:13px;font-weight:700;color:rgba(255,255,255,.85)">— {nm} 학생</span>'
                    f'<span style="font-size:11px;background:rgba(0,0,0,.2);color:#fff;padding:5px 16px;border-radius:var(--r-btn,100px);font-weight:800;border:1px solid rgba(255,255,255,.3)">{badge}</span>'
                    f'</div></div>'
                    f'<div style="background:var(--bg3);padding:48px 40px;display:flex;flex-direction:column;justify-content:center;gap:20px">'
                    f'<div style="display:inline-flex;align-items:center;gap:8px">'
                    f'<div style="width:32px;height:3px;background:var(--c1)"></div>'
                    f'<span style="font-size:10px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;color:var(--c1)">BEST REVIEW</span>'
                    f'</div>'
                    f'<p style="font-size:clamp(22px,2.5vw,32px);font-family:\'Black Han Sans\',var(--fh);font-weight:900;color:var(--text);line-height:1.3">이 수강생의<br>{d["subject"]} 공부가<br>완전히 달라졌습니다.</p>'
                    f'<p style="font-size:13px;line-height:1.9;color:var(--t70)">직접 경험한 변화를 그대로 담았습니다. 다음은 당신의 차례입니다.</p>'
                    f'</div></div>'
                )
            else:
                rh += (
                    f'<div class="rv d{min(i+1,4)}" style="display:flex;flex-direction:column;gap:14px;padding:32px;background:var(--bg3);border-radius:var(--r,4px);border:1px solid var(--bd);position:relative;overflow:hidden">'
                    f'<div style="position:absolute;top:-16px;right:12px;font-family:\'Black Han Sans\',var(--fh);font-size:100px;font-weight:900;color:var(--c1);opacity:.06;line-height:1;pointer-events:none">"</div>'
                    f'<div style="display:flex;gap:2px;color:#F59E0B;font-size:14px;position:relative;z-index:1">{"★"*5}</div>'
                    f'<p style="font-size:14px;line-height:1.95;font-weight:500;flex:1;position:relative;z-index:1;color:var(--text)">{strip_hanja(txt)}</p>'
                    f'<div style="display:flex;align-items:center;justify-content:space-between;padding-top:14px;border-top:1px solid var(--bd);position:relative;z-index:1">'
                    f'<div style="display:flex;align-items:center;gap:8px">'
                    f'<div style="width:28px;height:28px;border-radius:50%;background:var(--c1);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:900;color:#fff;flex-shrink:0">{nm[0] if nm else "익"}</div>'
                    f'<span style="font-size:12px;color:var(--t70);font-weight:600">— {nm} 학생</span>'
                    f'</div>'
                    f'<span style="font-size:10px;background:var(--bg);color:var(--c1);padding:4px 14px;border-radius:var(--r-btn,100px);font-weight:800;border:1.5px solid var(--c1)">{badge}</span>'
                    f'</div></div>'
                )
                    
        return (
            f'<section class="sec alt" id="reviews"><div style="max-width:1200px;margin:0 auto">'
            f'<div class="rv" style="margin-bottom:40px;display:flex;align-items:flex-end;justify-content:space-between">'
            f'<div><div class="tag-line">수강평</div><h2 class="sec-h2 st">생생한 수강생 후기</h2></div>'
            f'<div style="font-family:var(--fh);font-size:clamp(32px,4vw,52px);font-weight:900;color:var(--c1);opacity:.12;line-height:1">{len(reviews)}</div>'
            f'</div>'
            f'<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px">{rh}</div>'
            f'</div></section>'
        )
        
def sec_faq(d, cp, T):
    raw = cp.get("faqs",[
        ["수강 기간은 얼마나 되나요?","기본 30일이며, 연장권 구매 시 최대 90일까지 연장하실 수 있습니다. 학습 진도에 맞게 유연하게 조절 가능합니다."],
        ["교재는 별도 구매인가요?","별도 구매입니다. 수강 신청 페이지에서 강의와 함께 패키지로 구매하실 수 있으며, 패키지 구매 시 할인 혜택이 적용됩니다."],
        ["모바일에서도 수강 가능한가요?","PC, 태블릿, 스마트폰 모두 지원합니다. 앱에서 오프라인 다운로드도 가능하여 인터넷 없이도 학습하실 수 있습니다."],
    ])
    faqs = []
    for item in raw:
        if isinstance(item, dict): faqs.append([item.get("question",item.get("q","")), item.get("answer",item.get("a",""))])
        elif isinstance(item, list) and len(item)>=2: faqs.append([str(item[0]),str(item[1])])
    fh = ""
    for i,(q,a) in enumerate(faqs):
        fh += (
            f'<div class="rv d{min(i+1,3)}" style="margin-bottom:6px">'
            f'<details style="border:1px solid var(--bd);border-radius:var(--r,4px);overflow:hidden">'
            f'<summary style="padding:16px 22px;background:var(--bg3);display:flex;align-items:center;gap:12px;cursor:pointer;list-style:none;user-select:none">'
            f'<span style="color:var(--c1);font-weight:900;font-size:14px;flex-shrink:0;font-family:var(--fh)">Q.</span>'
            f'<span style="font-weight:700;font-size:14px;line-height:1.5;flex:1">{strip_hanja(q)}</span>'
            f'<span style="font-size:18px;color:var(--c1);flex-shrink:0;transition:transform .2s">＋</span>'
            f'</summary>'
            f'<div style="padding:18px 22px 20px;background:var(--bg);display:flex;gap:12px;align-items:flex-start;border-top:1px solid var(--bd)">'
            f'<span style="color:var(--t45);font-weight:700;font-size:14px;flex-shrink:0;font-family:var(--fh)">A.</span>'
            f'<p style="font-size:13.5px;line-height:1.9;color:var(--t70);margin:0">{strip_hanja(a)}</p>'
            f'</div></details></div>'
        )
    return (
        f'<section class="sec" id="faq">'
        f'<div style="display:grid;grid-template-columns:1fr 1.8fr;gap:72px;align-items:start;max-width:1200px;margin:0 auto">'
        f'<div class="rv" style="position:sticky;top:60px">'
        f'<div class="tag-line">FAQ</div>'
        f'<h2 class="sec-h2 st">자주 묻는 질문</h2>'
        f'<p class="sec-sub">궁금한 점을 클릭해 답변을 확인하세요.</p>'
        f'<div style="margin-top:24px;font-size:12px;color:var(--t45);line-height:1.8">더 궁금한 사항은<br>카카오톡 채널로 문의해 주세요.</div>'
        f'</div>'
        f'<div class="rv d1">{fh}</div>'
        f'</div></section>'
    )


def sec_cta(d, cp, T):
    tt    = strip_hanja(cp.get("ctaTitle", f"지금 바로 시작해<br>{d['subject']} 1등급을 확보하세요"))
    sub   = strip_hanja(cp.get("ctaSub",   f"{d['name']} 선생님과 함께라면 가능합니다." if d["name"] else f"{d['subject']} 1등급, 지금 시작하세요."))
    cc    = strip_hanja(cp.get("ctaCopy",  "지금 수강신청하기"))
    badge = strip_hanja(cp.get("ctaBadge", f"{d['target']} 전용"))
    ct    = _cta_text_color(T)  # ← 자동 텍스트 색상
    return (
        f'<section style="padding:clamp(80px,10vw,120px) clamp(28px,6vw,72px);text-align:center;position:relative;overflow:hidden;background:{T["cta"]}">'
        f'<div style="position:absolute;inset:0;background:radial-gradient(ellipse 70% 60% at 50% 0%,rgba(255,255,255,.07),transparent 60%);pointer-events:none"></div>'
        f'<div style="position:absolute;top:-200px;right:-200px;width:600px;height:600px;border-radius:50%;background:rgba(255,255,255,.04);pointer-events:none"></div>'
        f'<div style="position:absolute;bottom:-120px;left:-120px;width:500px;height:500px;border-radius:50%;background:rgba(255,255,255,.03);pointer-events:none"></div>'
        f'<div style="position:relative;z-index:1">'
        f'<div style="display:inline-flex;align-items:center;gap:8px;background:{ct["badge_bg"]};backdrop-filter:blur(8px);padding:7px 22px;border-radius:100px;font-size:10px;font-weight:800;color:{ct["txt"]};margin-bottom:28px;letter-spacing:.16em;text-transform:uppercase;border:1px solid {ct["badge_bd"]}">{badge}</div>'
        f'<h2 style="font-family:\'Black Han Sans\',var(--fh);font-size:clamp(32px,5.5vw,64px);font-weight:900;line-height:1.05;letter-spacing:-.02em;color:{ct["txt"]};margin-bottom:16px">{tt}</h2>'
        f'<p style="color:{ct["txt70"]};font-size:15px;line-height:1.9;margin-bottom:48px;max-width:460px;margin-left:auto;margin-right:auto">{sub}</p>'
        f'<div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap;align-items:center">'
        f'<a style="display:inline-flex;align-items:center;gap:10px;background:{ct["btn_bg"]};color:{ct["btn_col"]};font-weight:900;padding:18px 56px;border-radius:var(--r-btn,4px);font-size:17px;text-decoration:none;letter-spacing:.01em;box-shadow:0 8px 32px rgba(0,0,0,.18);transition:transform .15s" href="#">{cc} →</a>'
        f'<a style="display:inline-flex;align-items:center;gap:8px;background:{ct["btn2_bg"]};backdrop-filter:blur(8px);color:{ct["btn2_col"]};font-weight:700;padding:17px 36px;border-radius:var(--r-btn,4px);border:1.5px solid {ct["btn2_bd"]};font-size:15px;text-decoration:none" href="#">카카오톡 문의 💬</a>'
        f'</div>'
        f'<p style="margin-top:28px;font-size:11px;color:{ct["txt35"]};letter-spacing:.08em">지금 신청하는 수험생이 먼저 시작합니다</p>'
        f'</div></section>'
    )


def sec_event_overview(d, cp, T):
    t = strip_hanja(cp.get("eventTitle", d["purpose_label"]))
    desc = strip_hanja(cp.get("eventDesc","이 이벤트는 기간 한정으로 진행됩니다."))
    details = cp.get("eventDetails",[["📅","이벤트 기간","2026. 4. 1 — 4. 30"],["🎯","대상","고3·N수"],["💰","혜택","최대 30% 할인"]])
    dh = "".join(f'<div class="card rv d{i+1}" style="text-align:center;padding:32px 20px"><div style="font-size:36px;margin-bottom:14px">{ic}</div><div style="font-size:10px;font-weight:800;color:var(--c1);letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px">{lb}</div><div style="font-family:var(--fh);font-size:19px;font-weight:700">{vl}</div></div>' for i,(ic,lb,vl) in enumerate(details))
    return (f'<section class="sec" id="event-overview"><div style="max-width:1200px;margin:0 auto"><div class="rv"><div class="tag-line">이벤트 개요</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{desc}</p></div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px">{dh}</div></div></section>')


def sec_event_benefits(d, cp, T):
    t = strip_hanja(cp.get("benefitsTitle","이벤트 특별 혜택"))
    raw_b = cp.get("eventBenefits",[])
    defaults = [
        {"icon":"🎁","title":"수강료 특가","desc":"이벤트 기간 특별 할인 혜택을 제공합니다.","badge":"할인","no":"01"},
        {"icon":"📚","title":"교재 무료 제공","desc":"핵심 교재 및 학습 자료를 무료로 드립니다.","badge":"무료","no":"02"},
        {"icon":"🔥","title":"라이브 특강","desc":"매주 라이브 특강으로 실전 감각을 기릅니다.","badge":"매주","no":"03"},
    ]
    benefits = raw_b if isinstance(raw_b, list) and raw_b else defaults
    def _safe_b(b, i):
        if isinstance(b, dict):
            icon  = b.get("icon","✦")
            no    = b.get("no", f"{i+1:02d}")
            badge = strip_hanja(str(b.get("badge","혜택")))
            title = strip_hanja(str(b.get("title","")))
            desc  = strip_hanja(str(b.get("desc","")))
        else:
            icon, no, badge, title, desc = "✦", f"{i+1:02d}", "혜택", strip_hanja(str(b)), ""
        return (
            f'<div class="card rv d{min(i+1,4)}" style="display:grid;grid-template-columns:64px 1fr;gap:20px;align-items:flex-start;padding:24px">'
            f'<div style="width:64px;height:64px;border-radius:var(--r,4px);background:linear-gradient(135deg,var(--c1),var(--c2));display:flex;align-items:center;justify-content:center;font-size:28px;flex-shrink:0">{icon}</div>'
            f'<div><div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">'
            f'<span style="font-size:9px;font-weight:800;color:var(--c1);opacity:.7">NO.{no}</span>'
            f'<span style="background:var(--c1);color:#fff;font-size:9px;font-weight:800;padding:2px 10px;border-radius:100px">{badge}</span></div>'
            f'<div style="font-family:var(--fh);font-size:15px;font-weight:700;margin-bottom:7px" class="st">{title}</div>'
            f'<p style="font-size:12.5px;line-height:1.85;color:var(--t70)">{desc}</p>'
            f'</div></div>'
        )
    bh = "".join(_safe_b(b, i) for i, b in enumerate(benefits))
    return f'<section class="sec alt" id="event-benefits"><div style="max-width:1200px;margin:0 auto"><div class="rv"><div class="tag-line">이벤트 혜택</div><h2 class="sec-h2 st">{t}</h2></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px">{bh}</div></div></section>'


def sec_event_deadline(d, cp, T):
    t   = strip_hanja(cp.get("deadlineTitle","마감 안내"))
    msg = strip_hanja(cp.get("deadlineMsg","이벤트는 기간 한정으로 운영됩니다."))
    cc  = strip_hanja(cp.get("ctaCopy","이벤트 신청하기"))
    # JS 카운트다운 타이머 (72시간 후 기준)
    timer_html = (
        '<div id="cdtimer" style="display:flex;gap:16px;justify-content:center;margin:28px 0 36px">'
        + "".join(
            f'<div style="text-align:center;background:rgba(255,255,255,.12);border-radius:var(--r,4px);padding:14px 20px;min-width:72px">'
            f'<div id="cd_{unit}" style="font-family:var(--fh);font-size:36px;font-weight:900;color:#fff;line-height:1">00</div>'
            f'<div style="font-size:9px;font-weight:800;color:rgba(255,255,255,.5);letter-spacing:.14em;margin-top:4px">{label}</div>'
            f'</div>'
            for unit, label in [("d","DAYS"),("h","HOURS"),("m","MIN"),("s","SEC")]
        )
        + '</div>'
        + '<script>(function(){'
        + 'var end=new Date(Date.now()+72*60*60*1000);'
        + 'function upd(){'
        +   'var now=new Date(),diff=Math.max(0,end-now);'
        +   'var dd=Math.floor(diff/864e5),hh=Math.floor((diff%864e5)/36e5),'
        +       'mm=Math.floor((diff%36e5)/6e4),ss=Math.floor((diff%6e4)/1e3);'
        +   '[["cd_d",dd],["cd_h",hh],["cd_m",mm],["cd_s",ss]].forEach(function(x){'
        +     'var el=document.getElementById(x[0]);if(el)el.textContent=String(x[1]).padStart(2,"0");'
        +   '});'
        + '}'
        + 'upd();setInterval(upd,1000);'
        + '})();</script>'
    )
    return (
        f'<section id="event-deadline" style="padding:clamp(80px,10vw,120px) clamp(28px,6vw,72px);'
        f'text-align:center;position:relative;overflow:hidden;background:{T["cta"]}">'
        f'<div style="position:absolute;inset:0;background:radial-gradient(ellipse 60% 50% at 50% 100%,rgba(0,0,0,.4),transparent 70%);pointer-events:none"></div>'
        f'<div style="position:absolute;top:0;left:0;right:0;height:4px;background:rgba(255,255,255,.3)"></div>'
        f'<div class="rv" style="max-width:680px;margin:0 auto;position:relative;z-index:1">'
        f'<div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.15);'
        f'backdrop-filter:blur(8px);padding:7px 22px;border-radius:100px;font-size:11px;font-weight:800;'
        f'color:#fff;margin-bottom:24px;border:1px solid rgba(255,255,255,.25)">⏰ 마감 임박</div>'
        f'<h2 style="font-family:\'Black Han Sans\',var(--fh);font-size:clamp(28px,5vw,56px);'
        f'font-weight:900;line-height:1.05;color:#fff;margin-bottom:16px">{t}</h2>'
        f'<p style="color:rgba(255,255,255,.7);font-size:15px;line-height:1.9;max-width:460px;margin:0 auto 32px">{msg}</p>'
        f'{timer_html}'
        f'<div style="display:flex;gap:14px;justify-content:center;flex-wrap:wrap">'
        f'<a style="display:inline-flex;align-items:center;gap:10px;background:#fff;color:#0A0A0A;'
        f'font-weight:900;padding:18px 52px;border-radius:var(--r-btn,4px);font-size:17px;'
        f'text-decoration:none;box-shadow:0 8px 32px rgba(0,0,0,.25)" href="#">{cc} →</a>'
        f'<a style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.1);'
        f'backdrop-filter:blur(8px);color:rgba(255,255,255,.9);font-weight:700;padding:17px 32px;'
        f'border-radius:var(--r-btn,4px);border:1.5px solid rgba(255,255,255,.3);font-size:15px;'
        f'text-decoration:none" href="#">카카오톡 문의 💬</a>'
        f'</div>'
        f'<p style="margin-top:24px;font-size:11px;color:rgba(255,255,255,.35);letter-spacing:.06em">'
        f'마감 후 혜택은 제공되지 않습니다</p>'
        f'</div></section>'
    )


def sec_fest_hero(d, cp, T):
    t    = strip_hanja(cp.get("festHeroTitle", f"{d['subject']} 기획전"))
    cc   = strip_hanja(cp.get("festHeroCopy", "최고의 강사들이 한 자리에"))
    sub  = strip_hanja(cp.get("festHeroSub",  f"수능 {d['subject']} 전 강사 라인업."))
    stats  = cp.get("festHeroStats", [])
    bg_url = cp.get("bg_photo_url", "")

    # 배경 처리 — 이미지 있으면 오버레이 포함, 없으면 그라디언트
    if bg_url:
        hero_bg  = f"background:url('{bg_url}') center/cover no-repeat"
        overlay  = '<div style="position:absolute;inset:0;background:rgba(0,0,0,0.58);z-index:1;pointer-events:none"></div>'
        grad_overlay = '<div style="position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,.3) 0%,rgba(0,0,0,.7) 100%);z-index:1;pointer-events:none"></div>'
    else:
        hero_bg  = f"background:{T['cta']}"
        overlay  = ""
        grad_overlay = '<div style="position:absolute;inset:0;background:radial-gradient(ellipse 80% 70% at 50% 30%,rgba(255,255,255,.07),transparent 65%);pointer-events:none"></div>'

    sh = "".join(
        f'<div style="text-align:center">'
        f'<div style="font-family:var(--fh);font-size:clamp(22px,3.5vw,36px);font-weight:900;color:var(--c1)">{sv}</div>'
        f'<div style="font-size:9px;color:rgba(255,255,255,.5);font-weight:700;letter-spacing:.12em;text-transform:uppercase;margin-top:4px">{sl}</div>'
        f'</div>'
        for sv, sl in stats
    ) if stats else ""

    return (
        f'<section id="fest-hero" style="position:relative;min-height:80vh;overflow:hidden;'
        f'{hero_bg};display:flex;flex-direction:column;justify-content:center;'
        f'text-align:center;padding:clamp(80px,10vw,120px) clamp(28px,6vw,80px)">'
        + overlay
        + grad_overlay
        + f'<div style="position:relative;z-index:2">'
        + f'<div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.12);'
        +  f'backdrop-filter:blur(8px);padding:7px 22px;border-radius:var(--r-btn,4px);'
        +  f'font-size:11px;font-weight:800;color:#fff;margin-bottom:28px;'
        +  f'border:1px solid rgba(255,255,255,.2)">🏆 {d["subject"]} 기획전</div>'
        + f'<h1 style="font-family:\'Black Han Sans\',var(--fh);font-size:clamp(48px,9vw,128px);font-weight:900;'
        +  f'line-height:.88;letter-spacing:-.02em;color:#fff;margin-bottom:22px" class="st">{t}</h1>'
        + f'<p style="font-size:clamp(18px,2.5vw,24px);color:rgba(255,255,255,.85);'
        +  f'margin-bottom:12px;font-weight:700">{cc}</p>'
        + f'<p style="font-size:15px;color:rgba(255,255,255,.6);margin-bottom:52px;'
        +  f'max-width:500px;margin-left:auto;margin-right:auto">{sub}</p>'
        + (f'<div style="display:flex;gap:52px;justify-content:center;flex-wrap:wrap;'
           f'padding-top:40px;border-top:1px solid rgba(255,255,255,.15)">{sh}</div>' if sh else "")
        + f'</div></section>'
    )


def sec_fest_lineup(d, cp, T):
    t = strip_hanja(cp.get("festLineupTitle","강사 라인업"))
    s = strip_hanja(cp.get("festLineupSub",f"{d['subject']} 전 영역 최강 강사진"))
    lineup = cp.get("festLineup",[{"name":"강사A","tag":"독해·문법","tagline":"수능 영어 독해의 정석","badge":"베스트셀러","emoji":"📖"},{"name":"강사B","tag":"EBS 연계","tagline":"EBS 연계율 완벽 적중","badge":"적중률 1위","emoji":"🎯"},{"name":"강사C","tag":"어법·어휘","tagline":"어법·어휘 전문 빠른 풀이","badge":"속도UP","emoji":"⚡"},{"name":"강사D","tag":"파이널","tagline":"수능 D-30 파이널 완성","badge":"파이널 특화","emoji":"🏆"}])
    def _safe_l(l, i):
        if isinstance(l, dict):
            emoji   = l.get("emoji","📖")
            tag     = strip_hanja(str(l.get("tag","")))
            name    = strip_hanja(str(l.get("name","")))
            tagline = strip_hanja(str(l.get("tagline","")))
            badge   = strip_hanja(str(l.get("badge","")))
        else:
            emoji, tag, name, tagline, badge = "📖","강사","강사","강사 소개",""
        return (
            f'<div class="card rv d{min(i+1,4)}" style="text-align:center;padding:32px 24px">'
            f'<div style="font-size:44px;margin-bottom:16px">{emoji}</div>'
            f'<div style="display:inline-flex;align-items:center;gap:6px;background:var(--bg3);color:var(--c1);font-size:9.5px;font-weight:800;padding:4px 14px;border-radius:var(--r-btn,100px);margin-bottom:14px;border:1px solid var(--bd)">{tag}</div>'
            f'<div style="font-family:var(--fh);font-size:20px;font-weight:900;margin-bottom:9px" class="st">{name}</div>'
            f'<p style="font-size:12.5px;line-height:1.75;color:var(--t70);margin-bottom:14px">{tagline}</p>'
            f'<span style="font-size:10px;background:var(--c1);color:#fff;padding:4px 16px;border-radius:100px;font-weight:800">{badge}</span>'
            f'</div>'
        )
    lh = "".join(_safe_l(l, i) for i, l in enumerate(lineup))
    return f'<section class="sec alt" id="fest-lineup"><div style="max-width:1200px;margin:0 auto"><div class="rv"><div class="tag-line">강사 라인업</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{s}</p></div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px">{lh}</div></div></section>'


def sec_fest_benefits(d, cp, T):
    t = strip_hanja(cp.get("festBenefitsTitle","기획전 특별 혜택"))
    raw_b = cp.get("festBenefits",[])
    defaults = [
        {"icon":"🎁","title":"전 강사 통합 수강료 특가","desc":"최대 30% 추가 할인 혜택.","badge":"최대 30%","no":"01"},
        {"icon":"📚","title":"통합 학습 자료 무료","desc":"통합 교재 및 기출 자료 무료 제공.","badge":"무료 제공","no":"02"},
        {"icon":"🔥","title":"주간 라이브 특강","desc":"매주 전 강사 참여 라이브 특강.","badge":"전 강사","no":"03"},
        {"icon":"🏆","title":"목표 등급 보장","desc":"목표 등급 미달성 시 재수강 지원.","badge":"성적 보장","no":"04"},
    ]
    benefits = raw_b if isinstance(raw_b, list) and raw_b else defaults
    def _safe_fb(b, i):
        if isinstance(b, dict):
            icon  = b.get("icon","✦")
            no    = b.get("no", f"{i+1:02d}")
            badge = strip_hanja(str(b.get("badge","혜택")))
            title = strip_hanja(str(b.get("title","")))
            desc  = strip_hanja(str(b.get("desc","")))
        else:
            icon, no, badge, title, desc = "✦", f"{i+1:02d}", "혜택", strip_hanja(str(b)), ""
        return (
            f'<div class="card rv d{min(i+1,4)}" style="display:grid;grid-template-columns:64px 1fr;gap:20px;align-items:flex-start;padding:24px">'
            f'<div style="width:64px;height:64px;border-radius:var(--r,4px);background:linear-gradient(135deg,var(--c1),var(--c2));display:flex;align-items:center;justify-content:center;font-size:28px;flex-shrink:0">{icon}</div>'
            f'<div><div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">'
            f'<span style="font-size:9px;font-weight:800;color:var(--c1);opacity:.7">NO.{no}</span>'
            f'<span style="background:var(--c1);color:#fff;font-size:9px;font-weight:800;padding:2px 10px;border-radius:100px">{badge}</span></div>'
            f'<div style="font-family:var(--fh);font-size:15px;font-weight:700;margin-bottom:7px" class="st">{title}</div>'
            f'<p style="font-size:12.5px;line-height:1.85;color:var(--t70)">{desc}</p>'
            f'</div></div>'
        )
    bh = "".join(_safe_fb(b, i) for i, b in enumerate(benefits))
    return f'<section class="sec" id="fest-benefits"><div style="max-width:1200px;margin:0 auto"><div class="rv"><div class="tag-line">기획전 혜택</div><h2 class="sec-h2 st">{t}</h2></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px">{bh}</div></div></section>'


def sec_fest_cta(d, cp, T):
    t = strip_hanja(cp.get("festCtaTitle",f"지금 바로 {d['subject']} 기획전<br>전체 강사 라인업을 만나세요"))
    s = strip_hanja(cp.get("festCtaSub",f"최고의 강사들과 함께 {d['subject']} 1등급 완성."))
    return (f'<section style="padding:clamp(72px,10vw,112px) clamp(28px,6vw,72px);text-align:center;position:relative;overflow:hidden;background:{T["cta"]}"><div style="position:absolute;top:-120px;left:50%;transform:translateX(-50%);width:700px;height:700px;border-radius:50%;background:rgba(255,255,255,.03);pointer-events:none"></div><div style="position:relative;z-index:1"><div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.12);backdrop-filter:blur(8px);padding:7px 22px;border-radius:var(--r-btn,4px);font-size:11px;font-weight:800;color:#fff;margin-bottom:26px;border:1px solid rgba(255,255,255,.2)">🏆 {d["subject"]} 기획전 통합 신청</div><h2 style="font-family:var(--fh);font-size:clamp(28px,5vw,60px);font-weight:900;line-height:1.05;letter-spacing:-.04em;color:#fff;margin-bottom:18px">{t}</h2><p style="color:rgba(255,255,255,.6);font-size:15px;line-height:1.85;margin-bottom:44px;max-width:480px;margin-left:auto;margin-right:auto">{s}</p><div style="display:flex;gap:14px;justify-content:center;flex-wrap:wrap"><a style="display:inline-flex;align-items:center;gap:8px;background:#fff;color:#0A0A0A;font-weight:800;padding:18px 52px;border-radius:var(--r-btn,4px);font-size:16px;text-decoration:none" href="#">기획전 통합 신청 →</a><a style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.1);backdrop-filter:blur(8px);color:rgba(255,255,255,.82);font-weight:600;padding:17px 32px;border-radius:var(--r-btn,4px);border:1.5px solid rgba(255,255,255,.3);font-size:14px;text-decoration:none" href="#">강사 개별 신청</a></div></div></section>')
def gen_custom_sec(topic: str) -> dict:
    inst_ctx = _get_instructor_context()
    EVENT_KWS = ["이벤트", "후기", "수강평", "기대평", "경품", "추첨", "선물", "상품", "이벤", "기념"]
    is_event = any(kw in topic for kw in EVENT_KWS)

    if is_event:
        prompt = (
            f"수능 교육 랜딩페이지 이벤트 섹션 생성.\n\n"
            f"강사/과목: {inst_ctx}\n"
            f"이벤트 주제: \"{topic}\"\n"
            f"브랜드: {st.session_state.purpose_label}\n\n"
            f"규칙:\n"
            f"- title: 20자이내 임팩트 있는 이벤트 제목\n"
            f"- desc: 참여 독려 문장 40자이내\n"
            f"- prize_name: 실제 상품명 (예: [스타벅스] 아이스 아메리카노, [배스킨라빈스] 파인트)\n"
            f"- raffle_count: 추첨 인원 (예: \"30명\")\n"
            f"- event_details: 4행 이벤트 정보 (기간/대상/발표/혜택)\n"
            f"JSON만 반환:\n"
            f"{{\"tag\":\"{topic[:6]}\","
            f"\"title\":\"이벤트 제목 20자\","
            f"\"desc\":\"설명 40자\","
            f"\"event_style\":true,"
            f"\"prize_name\":\"상품명\","
            f"\"prize_img\":\"\","
            f"\"raffle_count\":\"30명\","
            f"\"event_details\":["
            f"[\"이벤트 기간\",\"2026. 04. 01(수) ~ 04. 30(목)\"],"
            f"[\"이벤트 대상\",\"강좌 수강생\"],"
            f"[\"당첨자 발표\",\"2026. 05. 07(목) 홈 공지\"],"
            f"[\"혜택\",\"상품명\"]]"
            f"}}"
        )
    else:
        prompt = (
            f"수능 교육 랜딩페이지의 추가 섹션을 만들어.\n\n"
            f"===강사/페이지 정보===\n{inst_ctx}\n"
            f"과목: {st.session_state.subject} | 브랜드: {st.session_state.purpose_label}\n\n"
            f"===섹션 주제===\n\"{topic}\"\n\n"
            f"===중요 규칙===\n"
            f"- 반드시 \"{topic}\" 주제로만 작성. 다른 내용 절대 금지\n"
            f"- tag: \"{topic[:6]}\" 관련 짧은 레이블\n"
            f"- title: 20자 이내 제목\n"
            f"- desc: 60자 이내 설명 문장\n"
            f"- items 각 desc: 45자 이상 구체적 설명\n"
            f"- 한자 금지\n\n"
            f"JSON만 반환:\n"
            f"{{\"tag\":\"{topic[:6]}\","
            f"\"title\":\"{topic} 안내\","
            f"\"desc\":\"{topic}에 대한 60자 내외 설명\","
            f"\"items\":["
            f"{{\"icon\":\"이모지\",\"title\":\"15자이내\",\"desc\":\"45자이상 구체적 설명\"}},"
            f"{{\"icon\":\"이모지\",\"title\":\"15자이내\",\"desc\":\"45자이상\"}}]"
            f"}}"
        )

    last_err = None
    for _attempt in range(3):
        try:
            return safe_json(call_ai(prompt, max_tokens=900))
        except Exception as e:
            last_err = e
            time.sleep(1)
    raise last_err
    
def _sec_event_promo(d: dict, c: dict, T: dict) -> str:
    """대성마이맥 스타일 이벤트 섹션 (상품+추첨배지+블랙라벨 정보표+입력폼) (가독성 및 색상 개선 버전)"""
    tag          = strip_hanja(c.get("tag", "이벤트"))
    title        = strip_hanja(c.get("title", "이벤트"))
    desc         = strip_hanja(c.get("desc", ""))
    prize_name   = strip_hanja(c.get("prize_name", ""))
    prize_img    = str(c.get("prize_img", ""))
    raffle_count = strip_hanja(str(c.get("raffle_count", "30명")))
    details      = c.get("event_details", [])
    
    # 1. 상품 이미지 & 원형 뱃지 (뱃지 색상 및 그림자 강조)
    num_only = ''.join(filter(str.isdigit, raffle_count)) if raffle_count else ""
    prize_visual = f'<div style="position:relative; display:inline-block; margin:0 auto;">'
    if raffle_count:
        prize_visual += (
            f'<div style="position:absolute; top:-10px; left:-20px; width:68px; height:68px; '
            f'background:#111; color:#fff; border-radius:50%; display:flex; flex-direction:column; '
            f'align-items:center; justify-content:center; box-shadow:0 6px 15px rgba(0,0,0,.3); z-index:2">'
            f'<span style="font-family:var(--fh); font-weight:900; font-size:22px; line-height:1">{num_only if num_only else "🎁"}</span>'
            f'<span style="font-size:11px; font-weight:700; margin-top:2px">{"명 추첨" if num_only else "추첨"}</span>'
            f'</div>'
        )
    if prize_img and prize_img.startswith("http"):
        prize_visual += f'<img src="{prize_img}" alt="{prize_name}" style="height:200px; object-fit:contain; position:relative; z-index:1">'
    else:
        prize_visual += (
            f'<div style="width:200px; height:200px; border-radius:50%; background:#fcfcfc; '
            f'border:2px dashed #ddd; display:flex; flex-direction:column; align-items:center; '
            f'justify-content:center; padding:20px; text-align:center; position:relative; z-index:1; box-shadow:inset 0 0 20px rgba(0,0,0,.02)">'
            f'<div style="font-size:56px; filter:drop-shadow(0 10px 10px rgba(0,0,0,.05))">🎁</div>'
            f'</div>'
        )
    prize_visual += f'</div>'

    # 2. 이벤트 정보 테이블 (블랙 라벨 스타일) (가독성 대폭 개선)
    detail_rows = "".join(
        f'<div style="display:flex; margin-bottom:4px; box-shadow:0 2px 8px rgba(0,0,0,.08); border-radius:4px; overflow:hidden;">'
        # 왼쪽 라벨 (진한 차콜, 흰색 글씨)
        f'<div style="width:110px; background:#1a1a1a; color:#fff; padding:12px; font-size:12.5px; '
        f'font-weight:700; display:flex; align-items:center; justify-content:center; letter-spacing:-0.02em; border-right:1px solid #333;">'
        f'{strip_hanja(str(row[0]))}</div>'
        # 오른쪽 값 (아주 연한 회색 배경, 진한 글씨 - 가독성 확보)
        f'<div style="flex:1; background:#f5f5f5; color:#222; padding:12px 18px; '
        f'font-size:13.5px; font-weight:600; display:flex; align-items:center;">{strip_hanja(str(row[1]))}</div>'
        f'</div>'
        for row in details if isinstance(row, (list, tuple)) and len(row) >= 2
    )

    # 3. 수강후기/기대평 입력 폼 (가독성 및 버튼 색상 개선)
    input_form = (
        f'<div style="background:#fff; padding:20px 24px; margin-top:32px; box-shadow:0 8px 30px rgba(0,0,0,.06); border:1px solid #eee; border-radius:4px;">'
        f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:16px;">'
        f'<span style="display:inline-flex; align-items:center; justify-content:center; width:16px; height:16px; '
        f'background:#D32F2F; color:#fff; border-radius:50%; font-size:11px; font-weight:900; line-height:1">!</span>'
        f'<span style="font-size:11.5px; color:#D32F2F; font-weight:600; letter-spacing:-0.02em;">'
        f'수강후기/기대평은 3개 이상의 강의 수강 시 작성할 수 있습니다. 단, 2개 이하의 강의로 구성된 강좌는 모든 강의를 수강해야 합니다.</span>'
        f'</div>'
        f'<div style="display:flex; gap:0; border:1px solid #ddd; border-radius:2px; overflow:hidden;">'
        f'<input type="text" placeholder="{title} 남기고 상품 받자!" '
        f'style="flex:1; padding:16px 20px; border:none; font-size:14px; outline:none; background:#fafafa; color:#333;" readonly>'
        # 버튼을 완전한 '블랙 라벨' 스타일로 검은색으로 변경
        f'<button style="background:#111; color:#fff; border:none; padding:0 36px; font-weight:800; font-size:14px; cursor:pointer; transition:background 0.2s;" '
        f'onmouseover="this.style.background=\'#000\'" onmouseout="this.style.background=\'#111\'">작성하기</button>'
        f'</div>'
        f'</div>'
    )

    prize_name_html = f'<div style="margin-top:20px; font-size:14px; font-weight:800; color:#333; text-align:center;">{prize_name}</div>' if prize_name else ""

    # 4. 전체 HTML 조립 (헤더 색상 개선 및 섹션 배경색 고정)
    return (
        # 'sec alt' 클래스 대신 스타일을 직접 지정하여 흰색 배경으로 고정
        f'<section class="sec" style="background:#fff" id="custom-section">'
        f'<div style="max-width:860px; margin:0 auto">'
        f'<div class="rv" style="text-align:center; margin-bottom:48px">'
        # 태그 라인 색상 및 배경 개선
        f'<div style="display:inline-flex; align-items:center; gap:8px; border:1px solid #aaa; color:#666; '
        f'font-size:11px; font-weight:800; padding:6px 20px; border-radius:100px; margin-bottom:20px; '
        f'letter-spacing:0.1em; background:#fafafa;">{tag} EVENT</div>'
        # 제목 및 설명 색상 개선
        f'<h2 style="font-family:\'Black Han Sans\', var(--fh); font-size:clamp(32px, 5vw, 48px); font-weight:900; '
        f'line-height:1.15; letter-spacing:-0.03em; color:#111; margin-bottom:16px;">{title}</h2>'
        f'<p style="font-size:15.5px; line-height:1.85; color:#444; font-weight:500; '
        f'max-width:600px; margin:0 auto">{desc}</p>'
        f'</div>'
        # 이벤트 카드 배경색 및 테두리 개선
        f'<div class="rv d1" style="background:#F4F4F4; padding:40px; border-radius:var(--r,8px); box-shadow:0 12px 40px rgba(0,0,0,.15); border:1px solid #ddd;">'
        f'<div style="display:grid; grid-template-columns:1fr 1.3fr; gap:40px; align-items:center;">'
        f'<div style="text-align:center;">'
        f'{prize_visual}'
        f'{prize_name_html}'
        f'</div>'
        f'<div>{detail_rows}</div>'
        f'</div>'
        f'</div>'
        f'<div class="rv d2">{input_form}</div>'
        f'</div></section>'
    )


def sec_custom(d, cp, T):
    """기타 섹션 — 메인 분기 처리"""
    c = cp.get("custom_section_data", {})
    if not c: return ""
    
    # 안전장치: AI가 event_style을 안 주더라도, 상품명이나 이벤트 표가 있으면 무조건 이벤트 폼으로 렌더링
    is_event = c.get("event_style") or "event_details" in c or "prize_name" in c or "raffle_count" in c
    
    if is_event:
        return _sec_event_promo(d, c, T)

    # 이벤트가 아닌 일반 섹션 (이전의 카드/텍스트 레이아웃)
    tag   = strip_hanja(c.get("tag", "추가 안내"))
    title = strip_hanja(c.get("title", "추가 섹션"))
    items = c.get("items", [])
    desc  = strip_hanja(c.get("desc", ""))

    if items:
        ih = "".join(
            f'<div class="card rv d{min(i+1,3)}">'
            f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">'
            f'<div style="width:40px;height:40px;min-width:40px;border-radius:var(--r,4px);'
            f'background:var(--c1);display:flex;align-items:center;justify-content:center;'
            f'font-size:18px">{it.get("icon","✦")}</div>'
            f'<div style="font-family:var(--fh);font-size:14px;font-weight:700" class="st">'
            f'{strip_hanja(it.get("title",""))}</div></div>'
            f'<p style="font-size:12.5px;line-height:1.9;color:var(--t70)">'
            f'{strip_hanja(it.get("desc",""))}</p>'
            f'</div>'
            for i, it in enumerate(items)
        )
        cols = f"repeat({min(len(items),3)},1fr)"
        body = f'<div style="display:grid;grid-template-columns:{cols};gap:14px" class="rv d1">{ih}</div>'
    else:
        body = f'<div class="rv d1"><p style="font-size:14px;line-height:1.9;color:var(--t70)">{desc}</p></div>'

    return (
        f'<section class="sec" id="custom-section">'
        f'<div style="max-width:1200px;margin:0 auto">'
        f'<div class="rv"><div class="tag-line">{tag}</div>'
        f'<h2 class="sec-h2 st">{title}</h2></div>'
        f'{body}</div></section>'
    )


# ══════════════════════════════════════════════════════
# 추가 고급 섹션들 (ABPS / OVS 시안 수준)
# ══════════════════════════════════════════════════════
def sec_before_after(d, cp, T):
    t   = strip_hanja(cp.get('baTitle', '공부 방식이 이렇게 달라집니다'))
    sub = strip_hanja(cp.get('baSub', f"{d['purpose_label']} 이후의 변화"))
    befores = cp.get('baBeforeItems', [
        f"{d['subject']} 지문이 무슨 말인지 몰라 처음부터 다 읽는다",
        '시간이 부족해 뒷문제를 찍는 일이 반복된다',
        '아는 내용인데 시험장에서 실수가 계속 나온다',
    ])
    afters = cp.get('baAfterItems', [
        '구조가 보여서 필요한 부분만 정확히 읽는다',
        '시간이 10분 이상 남아 검토까지 완료한다',
        '실전에서 배운 대로 정확히 풀어낸다',
    ])
    bh = ''.join(
        f'<div style="display:flex;gap:12px;align-items:flex-start;'
        f'padding:14px 0;border-bottom:1px solid rgba(255,80,80,.12)">'
        f'<div style="flex-shrink:0;width:22px;height:22px;border-radius:50%;'
        f'background:rgba(255,80,80,.2);border:1.5px solid #FF5050;'
        f'display:flex;align-items:center;justify-content:center;'
        f'font-size:11px;color:#FF5050;font-weight:900;margin-top:1px">✕</div>'
        f'<p style="font-size:14px;line-height:1.75;color:rgba(255,255,255,.7);margin:0">'
        f'{strip_hanja(b)}</p></div>'
        for b in befores
    )
    ah = ''.join(
        f'<div style="display:flex;gap:12px;align-items:flex-start;'
        f'padding:14px 0;border-bottom:1px solid var(--bd)">'
        f'<div style="flex-shrink:0;width:22px;height:22px;border-radius:50%;'
        f'background:var(--c1);display:flex;align-items:center;justify-content:center;'
        f'font-size:11px;color:#fff;font-weight:900;margin-top:1px">✓</div>'
        f'<p style="font-size:14px;line-height:1.75;color:var(--text);margin:0;font-weight:500">'
        f'{strip_hanja(a)}</p></div>'
        for a in afters
    )
    return (
        f'<section class="sec" id="before-after">'
        f'<div style="max-width:1000px;margin:0 auto">'
        f'<div class="rv" style="text-align:center;margin-bottom:40px">'
        f'<div class="tag-line" style="justify-content:center">수강 전/후</div>'
        f'<h2 class="sec-h2 st" style="text-align:center">{t}</h2>'
        f'<p class="sec-sub" style="text-align:center;margin:0 auto">{sub}</p>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:1fr 48px 1fr;gap:0;align-items:stretch" class="rv d1">'
        f'<div style="background:#1A0808;border-radius:var(--r,4px) 0 0 var(--r,4px);'
        f'padding:28px;border:1px solid rgba(255,80,80,.2);border-right:none">'
        f'<div style="font-size:11px;font-weight:800;color:#FF5050;letter-spacing:.14em;'
        f'text-transform:uppercase;margin-bottom:16px;display:flex;align-items:center;gap:8px">'
        f'<div style="width:8px;height:8px;border-radius:50%;background:#FF5050"></div>BEFORE</div>'
        f'{bh}</div>'
        f'<div style="background:var(--c1);display:flex;align-items:center;justify-content:center">'
        f'<div style="font-size:18px;font-weight:900;color:#fff">→</div>'
        f'</div>'
        f'<div style="background:var(--bg3);border-radius:0 var(--r,4px) var(--r,4px) 0;'
        f'padding:28px;border:1px solid var(--bd);border-left:none">'
        f'<div style="font-size:11px;font-weight:800;color:var(--c1);letter-spacing:.14em;'
        f'text-transform:uppercase;margin-bottom:16px;display:flex;align-items:center;gap:8px">'
        f'<div style="width:8px;height:8px;border-radius:50%;background:var(--c1)"></div>AFTER</div>'
        f'{ah}</div>'
        f'</div>'
        f'</div></section>'
    )
def sec_video(d, cp, T):
    yt_url  = cp.get('videoUrl', '')
    title   = strip_hanja(cp.get('videoTitle', f"{d['name']} 선생님 강의 미리보기"))
    sub     = strip_hanja(cp.get('videoSub', f"{d['subject']} 공부의 본질이 바뀝니다."))
    tag     = cp.get('videoTag', 'OFFICIAL TRAILER')

    if yt_url and 'youtube' in yt_url:
        embed = (
            f'<div style="position:relative;width:100%;padding-bottom:56.25%;'
            f'border-radius:var(--r,4px);overflow:hidden;border:1px solid var(--bd)">'
            f'<iframe src="{yt_url}" style="position:absolute;inset:0;width:100%;height:100%;border:none"'
            f' allowfullscreen allow="autoplay;encrypted-media"></iframe></div>'
        )
    else:
        embed = (
            f'<div style="position:relative;width:100%;padding-bottom:52%;'
            f'background:var(--bg3);border-radius:var(--r,4px);overflow:hidden;'
            f'border:1px solid var(--bd)">'
            f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;'
            f'align-items:center;justify-content:center;gap:14px">'
            f'<div style="width:64px;height:64px;border-radius:50%;background:var(--c1);'
            f'display:flex;align-items:center;justify-content:center">'
            f'<div style="width:0;height:0;border-style:solid;'
            f'border-width:12px 0 12px 24px;'
            f'border-color:transparent transparent transparent #fff;margin-left:5px"></div>'
            f'</div>'
            f'<div style="font-size:13px;color:var(--t45);font-weight:600">'
            f'사이드바에서 YouTube URL을 입력하면 영상이 표시됩니다</div>'
            f'</div></div>'
        )

    return (
        f'<section class="sec alt" id="video">'
        f'<div style="max-width:960px;margin:0 auto">'
        f'<div class="rv" style="text-align:center;margin-bottom:32px">'
        f'<div style="display:inline-flex;align-items:center;gap:8px;background:var(--c1);'
        f'color:#fff;font-size:10px;font-weight:800;padding:5px 16px;'
        f'border-radius:var(--r-btn,4px);margin-bottom:14px;letter-spacing:.14em">▶ {tag}</div>'
        f'<h2 class="sec-h2 st" style="text-align:center;font-size:clamp(20px,3vw,34px)">{title}</h2>'
        f'<p class="sec-sub" style="text-align:center;margin:0 auto">{sub}</p>'
        f'</div>'
        f'<div class="rv d1">{embed}</div>'
        f'</div></section>'
    )


def sec_grade_stats(d, cp, T):
    """등급 변화 시각화 — 이름·기간·요약 통계 포함"""
    t   = strip_hanja(cp.get("gradeTitle", "숫자가 증명하는 변화"))
    sub = strip_hanja(cp.get("gradeSub",   f"{d['subject']} 수강 후 실제로 달라진 수강생들"))

    changes = cp.get("gradeChanges", [
        {"before":"4","after":"1","name":"고3 김OO","period":"4개월 수강"},
        {"before":"3","after":"1","name":"N수 이OO","period":"3개월 수강"},
        {"before":"4","after":"2","name":"고3 박OO","period":"3개월 수강"},
        {"before":"5","after":"2","name":"N수 최OO","period":"5개월 수강"},
        {"before":"3","after":"1","name":"고3 정OO","period":"4개월 수강"},
        {"before":"6","after":"3","name":"N수 한OO","period":"6개월 수강"},
        {"before":"4","after":"1","name":"고3 윤OO","period":"4개월 수강"},
        {"before":"2","after":"1","name":"고3 송OO","period":"2개월 수강"},
    ])

    # 요약 통계 계산
    improvements, ones = [], 0
    for c in changes:
        try:
            diff = int(c.get("before","0")) - int(c.get("after","0"))
            improvements.append(diff)
            if c.get("after","") == "1": ones += 1
        except: pass
    avg_up = sum(improvements)/len(improvements) if improvements else 0

    # 요약 통계 바
    summary_html = (
        f'<div class="rv" style="display:grid;grid-template-columns:repeat(3,1fr);'
        f'gap:1px;background:var(--bd);border-radius:var(--r,4px);overflow:hidden;margin-bottom:28px">'
        + "".join(
            f'<div style="background:var(--bg3);padding:22px 12px;text-align:center">'
            f'<div style="font-family:var(--fh);font-size:clamp(26px,3vw,38px);font-weight:900;color:var(--c1)">{val}</div>'
            f'<div style="font-size:11px;color:var(--t70);margin-top:5px;font-weight:700">{label}</div>'
            f'</div>'
            for val, label in [
                (f"{ones}명", "1등급 달성"),
                (f"평균 {avg_up:.1f}등급", "상승 폭"),
                (f"{len(changes)}개", "성공 사례"),
            ]
        ) + f'</div>'
    )

    # 카드 그리드
    cards_html = "".join(
        f'<div class="rv d{min(i%4+1,4)}" style="background:var(--bg3);border-radius:var(--r,4px);'
        f'border:1px solid var(--bd);overflow:hidden">'
        # 상단: 이름 + 기간 뱃지
        f'<div style="padding:9px 12px;border-bottom:1px solid var(--bd);'
        f'display:flex;justify-content:space-between;align-items:center">'
        f'<span style="font-size:10px;font-weight:700;color:var(--t70)">{c.get("name",f"수강생 {i+1:02d}")}</span>'
        f'<span style="font-size:8.5px;background:var(--c1);color:#fff;padding:2px 8px;'
        f'border-radius:100px;font-weight:800;white-space:nowrap">{c.get("period","수강 완료")}</span>'
        f'</div>'
        # 하단: 등급 변화
        f'<div style="padding:14px 10px;display:flex;align-items:center;justify-content:center;gap:6px">'
        f'<div style="text-align:center">'
        f'<div style="font-family:var(--fh);font-size:clamp(22px,2.8vw,34px);font-weight:900;'
        f'color:var(--t45);line-height:1;text-decoration:line-through;text-decoration-color:rgba(255,80,80,.6)">{c.get("before","?")}</div>'
        f'<div style="font-size:8px;font-weight:700;color:var(--t45);margin-top:2px">등급</div>'
        f'</div>'
        f'<div style="display:flex;flex-direction:column;align-items:center;gap:1px">'
        f'<div style="font-size:14px;color:var(--c1)">→</div>'
        f'<div style="font-size:7.5px;font-weight:800;color:var(--c1);letter-spacing:.04em;white-space:nowrap">'
        f'+{int(c.get("before","0"))-int(c.get("after","0"))}등급</div>'
        f'</div>'
        f'<div style="text-align:center">'
        f'<div style="font-family:var(--fh);font-size:clamp(28px,3.5vw,44px);font-weight:900;'
        f'color:var(--c1);line-height:1">{c.get("after","?")}</div>'
        f'<div style="font-size:8px;font-weight:800;color:var(--c1);margin-top:2px">등급</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        for i, c in enumerate(changes)
        if c.get("before","").isdigit() and c.get("after","").isdigit()
    )

    return (
        f'<section class="sec alt" id="grade-stats">'
        f'<div style="max-width:1000px;margin:0 auto">'
        f'<div class="rv" style="text-align:center;margin-bottom:28px">'
        f'<div class="tag-line" style="justify-content:center">수강 성과</div>'
        f'<h2 class="sec-h2 st" style="text-align:center">{t}</h2>'
        f'<p class="sec-sub" style="text-align:center;margin:0 auto">{sub}</p>'
        f'</div>'
        f'{summary_html}'
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px">{cards_html}</div>'
        f'<p class="rv d2" style="text-align:center;font-size:10.5px;color:var(--t45);margin-top:14px">'
        f'* 실제 수강생의 성적 변화 사례를 정리한 것입니다. 개인차가 있을 수 있습니다.</p>'
        f'</div></section>'
    )


def sec_method(d, cp, T):
    """시그니처 학습법 시각화 — ABPS 'Apply to text' 스타일"""
    t    = strip_hanja(cp.get("methodTitle", f"{d['name'] or d['subject']} 시그니처 학습법"))
    sub  = strip_hanja(cp.get("methodSub",   "이 방식으로 접근하면 지문이 완전히 달리 보입니다"))
    methods_raw = cp.get("methodSteps",[])
    ip = st.session_state.get("inst_profile") or {}
    sig = [strip_hanja(m) for m in (ip.get("signatureMethods") or []) if m and m not in ("없음","")]
    if not methods_raw:
        methods_raw = [
            {"step": s, "label": f"{i+1}단계", "desc": f"{s} 방식으로 {d['subject']} 지문에 접근합니다."}
            for i, s in enumerate(sig[:4])
        ] if sig else [
            {"step":"STEP 01","label":"파악","desc":f"{d['subject']} 구조를 파악합니다."},
            {"step":"STEP 02","label":"분석","desc":"핵심 논리를 분석합니다."},
            {"step":"STEP 03","label":"적용","desc":"실전 문제에 즉시 적용합니다."},
        ]
    steps_html = ""
    for i, m in enumerate(methods_raw):
        s  = strip_hanja(str(m.get("step",  f"STEP {i+1:02d}")))
        lb = strip_hanja(str(m.get("label", f"{i+1}단계")))
        dc = strip_hanja(str(m.get("desc",  "")))
        steps_html += (
            f'<div class="rv d{min(i+1,4)}" style="display:flex;gap:0;align-items:stretch;margin-bottom:10px">'
            # 좌: 스텝 번호 블록
            f'<div style="min-width:90px;background:var(--c1);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:18px 12px;border-radius:var(--r,4px) 0 0 var(--r,4px)">'
            f'<div style="font-family:var(--fh);font-size:11px;font-weight:900;color:rgba(255,255,255,.6);letter-spacing:.1em">{s}</div>'
            f'<div style="font-family:var(--fh);font-size:17px;font-weight:900;color:#fff;margin-top:2px">{lb}</div>'
            f'</div>'
            # 우: 설명
            f'<div style="flex:1;background:var(--bg3);padding:18px 24px;border-radius:0 var(--r,4px) var(--r,4px) 0;border:1px solid var(--bd);border-left:none;display:flex;align-items:center">'
            f'<p style="font-size:14px;line-height:1.8;color:var(--text);margin:0;font-weight:500">{dc}</p>'
            f'</div></div>'
        )
    return (
        f'<section class="sec alt" id="method">'
        f'<div style="display:grid;grid-template-columns:1fr 1.4fr;gap:72px;align-items:center;max-width:1200px;margin:0 auto">'
        f'<div class="rv" style="position:sticky;top:60px">'
        f'<div class="tag-line">학습법</div>'
        f'<h2 class="sec-h2 st">{t}</h2>'
        f'<p class="sec-sub">{sub}</p>'
        f'<div style="margin-top:24px;padding:20px 24px;border:1.5px solid var(--c1);border-radius:var(--r,4px)">'
        f'<div style="font-size:10px;font-weight:800;letter-spacing:.14em;color:var(--c1);text-transform:uppercase;margin-bottom:8px">핵심 공식</div>'
        f'<div style="font-family:var(--fh);font-size:clamp(18px,2vw,24px);font-weight:900;color:var(--text)">'
        + (" → ".join(sig[:3]) if sig else f"{d['subject']} 완성 공식")
        + f'</div></div></div>'
        f'<div class="rv d1">{steps_html}</div>'
        f'</div></section>'
    )


def sec_package(d, cp, T):
    """구매 패키지 섹션 — OVS 스타일 교재/패키지 안내"""
    t    = strip_hanja(cp.get("pkgTitle",   f"{d['purpose_label']} 구성 안내"))
    sub  = strip_hanja(cp.get("pkgSub",     "지금 신청하면 아래 구성이 모두 포함됩니다"))
    pkgs = cp.get("packages",[
        {"icon":"📗","name":"강의 수강권","desc":f"{d['purpose_label']} 전체 강의 무제한 수강","badge":"필수"},
        {"icon":"📖","name":"PDF 교재","desc":"핵심 이론·기출 정리 PDF 파일 제공","badge":"포함"},
        {"icon":"🎯","name":"실전 모의고사","desc":"단계별 실전 모의고사 3회분 제공","badge":"포함"},
        {"icon":"💬","name":"질문 게시판","desc":"강사 직접 답변 질문 게시판 무제한 이용","badge":"특전"},
    ])
    ph = "".join(
        f'<div class="rv d{min(i+1,4)}" style="display:flex;gap:16px;align-items:center;padding:18px 22px;border:1px solid var(--bd);border-radius:var(--r,4px);background:var(--bg);margin-bottom:8px">'
        f'<div style="font-size:32px;flex-shrink:0">{p.get("icon","📦") if isinstance(p,dict) else "📦"}</div>'
        f'<div style="flex:1">'
        f'<div style="font-family:var(--fh);font-size:15px;font-weight:700;color:var(--text);margin-bottom:3px" class="st">{strip_hanja(str(p.get("name","") if isinstance(p,dict) else p))}</div>'
        f'<p style="font-size:12.5px;line-height:1.7;color:var(--t70);margin:0">{strip_hanja(str(p.get("desc","") if isinstance(p,dict) else ""))}</p>'
        f'</div>'
        + (lambda _b: f'<span style="flex-shrink:0;font-size:10px;font-weight:800;background:{"var(--c1)" if _b=="필수" else "var(--bg3)"};color:{"#fff" if _b=="필수" else "var(--c1)"};padding:5px 14px;border-radius:var(--r-btn,100px);border:1.5px solid var(--c1)">{_b}</span>')(strip_hanja(str(p.get("badge","포함") if isinstance(p,dict) else "포함")))
        + f'</div>'
        for i, p in enumerate(pkgs)
    )
    return (
        f'<section class="sec" id="package">'
        f'<div style="max-width:900px;margin:0 auto">'
        f'<div class="rv" style="text-align:center;margin-bottom:36px">'
        f'<div class="tag-line" style="justify-content:center">구성 안내</div>'
        f'<h2 class="sec-h2 st" style="text-align:center">{t}</h2>'
        f'<p class="sec-sub" style="text-align:center">{sub}</p>'
        f'</div>'
        f'<div class="rv d1">{ph}</div>'
        f'</div></section>'
    )


# ══════════════════════════════════════════════════════
# HTML 빌더
# ══════════════════════════════════════════════════════
def build_html(secs: list) -> str:
    T  = get_theme()
    cp = dict(st.session_state.custom_copy or {})
    if st.session_state.get("uploaded_bg_b64"):
        cp["bg_photo_url"] = st.session_state.uploaded_bg_b64
    elif st.session_state.bg_photo_url:
        cp["bg_photo_url"] = st.session_state.bg_photo_url
    d = {"name":st.session_state.instructor_name or "",
         "subject":st.session_state.subject,
         "purpose_label":st.session_state.purpose_label,
         "target":st.session_state.target}
    # heroStyle 결정
    if st.session_state.concept == "custom" and st.session_state.custom_theme:
        T["heroStyle"] = st.session_state.custom_theme.get("heroStyle","typographic")
    else:
        T["heroStyle"] = THEMES.get(st.session_state.concept,{}).get("heroStyle","typographic")
    # dark 테마 카드 보정
    dc = ".card{background:var(--bg2)!important}" if T["dark"] else ""
    mp = {
        "banner":sec_banner,"intro":sec_intro,"why":sec_why,"curriculum":sec_curriculum,
        "target":sec_target,"reviews":sec_reviews,"faq":sec_faq,"cta":sec_cta,
        "video":sec_video,"before_after":sec_before_after,"method":sec_method,"package":sec_package,
        "grade_stats":sec_grade_stats, 
        "event_overview":sec_event_overview,"event_benefits":sec_event_benefits,
        "event_deadline":sec_event_deadline,"fest_hero":sec_fest_hero,
        "fest_lineup":sec_fest_lineup,"fest_benefits":sec_fest_benefits,
        "fest_cta":sec_fest_cta,"custom_section":sec_custom,
    }
    # 네비게이션 섹션 레이블 맵
    NAV_LABELS = {
        "banner":"홈","intro":"강사 소개","why":"수강 이유",
        "curriculum":"커리큘럼","target":"수강 대상","reviews":"수강평",
        "faq":"FAQ","cta":"수강신청",
        "video":"미리보기","before_after":"수강 전/후","method":"학습법","package":"구성",
        "event_overview":"이벤트","event_benefits":"혜택","event_deadline":"마감",
        "fest_hero":"기획전","fest_lineup":"라인업","fest_benefits":"혜택","fest_cta":"신청",
    }
    nav_items = [s for s in secs if s in NAV_LABELS and s != "banner"]
    nav_id_map = {
        "intro":"intro","why":"why","curriculum":"curriculum","target":"target",
        "reviews":"reviews","faq":"faq","cta":"cta","video":"video",
        "before_after":"before-after","method":"method","package":"package",
        "event_overview":"event-overview","event_benefits":"event-benefits",
        "event_deadline":"event-deadline","fest_hero":"fest-hero",
        "fest_lineup":"fest-lineup","fest_benefits":"fest-benefits","fest_cta":"fest-cta",
    }
    nav_html = (
        f'<nav id="site-nav" style="position:fixed;top:0;left:0;right:0;z-index:9990;'
        f'background:rgba(0,0,0,0);backdrop-filter:blur(0px);-webkit-backdrop-filter:blur(0px);'
        f'border-bottom:1px solid transparent;transition:all .35s cubic-bezier(.16,1,.3,1);padding:0">'
        f'<div style="max-width:1200px;margin:0 auto;padding:0 clamp(20px,4vw,60px);'
        f'display:flex;align-items:center;justify-content:space-between;height:56px">'
        # 로고
        f'<div style="font-family:\'Black Han Sans\',var(--fh);font-size:16px;font-weight:900;'
        f'color:#fff;letter-spacing:.04em;white-space:nowrap">'
        f'{d["name"] if d["name"] else d["subject"]} <span style="color:var(--c1)">·</span> {d["subject"]}</div>'
        # 메뉴
        f'<div style="display:flex;align-items:center;gap:4px;overflow-x:auto;scrollbar-width:none">'
        + "".join(
            f'<a href="#{nav_id_map.get(s,s)}" style="font-size:11px;font-weight:700;'
            f'color:rgba(255,255,255,.65);padding:6px 12px;border-radius:var(--r-btn,4px);'
            f'text-decoration:none;white-space:nowrap;transition:color .15s,background .15s;'
            f'letter-spacing:.04em" '
            f'onmouseover="this.style.color=\'#fff\';this.style.background=\'rgba(255,255,255,.1)\'" '
            f'onmouseout="this.style.color=\'rgba(255,255,255,.65)\';this.style.background=\'transparent\'">'
            f'{NAV_LABELS.get(s,s)}</a>'
            for s in nav_items[:7]
        )
        + f'</div>'
        # CTA 버튼
        f'<a href="#cta" class="btn-p" style="font-size:11px;padding:8px 20px;flex-shrink:0;'
        f'margin-left:12px">수강신청 →</a>'
        f'</div></nav>'
        # 네비 스크롤 JS
        f'<script>'
        f'(function(){{'
        f'var nav=document.getElementById("site-nav");'
        f'var scrolled=false;'
        f'window.addEventListener("scroll",function(){{'
        f'if(window.scrollY>80){{if(!scrolled){{'
        f'nav.style.background="rgba(10,10,18,.92)";'
        f'nav.style.backdropFilter="blur(20px)";'
        f'nav.style.webkitBackdropFilter="blur(20px)";'
        f'nav.style.borderBottomColor="rgba(255,255,255,.08)";'
        f'nav.style.padding="0";'
        f'scrolled=true;'
        f'}}}}else{{if(scrolled){{'
        f'nav.style.background="rgba(0,0,0,0)";'
        f'nav.style.backdropFilter="blur(0px)";'
        f'nav.style.webkitBackdropFilter="blur(0px)";'
        f'nav.style.borderBottomColor="transparent";'
        f'scrolled=false;'
        f'}}}}'
        f'}});'
        f'}})();'
        f'</script>'
    )
    body = nav_html + "\n".join(mp[s](d,cp,T) for s in secs if s in mp)
    ttl  = cp.get("bannerTitle", cp.get("festHeroTitle", d["purpose_label"]))
    particle_js = _particle_js(T.get("particle","none"))
    concept_key = st.session_state.concept if st.session_state.concept != "custom" else "custom"
    return (
    f'<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"/>'
    f'<meta name="viewport" content="width=device-width,initial-scale=1.0"/>'
    f'<title>{d["name"]} {d["subject"]} · {ttl}</title>'
    f'<link rel="preconnect" href="https://fonts.googleapis.com"/>'
    f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>'
    f'<link href="https://fonts.googleapis.com/css2?family=Black+Han+Sans&display=swap" rel="stylesheet"/>'
    f'<link href="{T["fonts"]}" rel="stylesheet"/>'
    f'<style>:root{{{T["vars"]}}}{BASE_CSS}{T["extra_css"]}{dc}</style>'
    f'</head><body>{body}'
    + _particle_js(T.get("particle","none"))
    + _theme_fx(concept_key)
    + f'<script>'
    + f'const ro=new IntersectionObserver(es=>{{es.forEach(e=>{{if(e.isIntersecting){{'
    + f'e.target.classList.add("on");ro.unobserve(e.target);}}}});}},{{threshold:.06,rootMargin:"0px 0px -40px 0px"}});'
    + f'document.querySelectorAll(".rv,.rv-left,.rv-right").forEach(el=>ro.observe(el));'
    + f'</script>'
    + f'<button id="mode-toggle" onclick="(function(){{var b=document.body;b.classList.toggle(\'light-mode\');localStorage.setItem(\'mode\',b.classList.contains(\'light-mode\')?\' light\':\'dark\');this.textContent=b.classList.contains(\'light-mode\')?\'🌙\':\'☀️\'}}).call(this)" title="다크/라이트 모드">☀️</button>'
    + f'<script>(function(){{var m=localStorage.getItem(\'mode\');var btn=document.getElementById(\'mode-toggle\');if(m===\'light\'){{document.body.classList.add(\'light-mode\');if(btn)btn.textContent=\'🌙\'}}}})()</script>'
    + f'</body></html>'
)

# ══════════════════════════════════════════════════════
# UI CSS (사이드바 + 메인)
# ══════════════════════════════════════════════════════
st.markdown("""<style>
[data-testid="stSidebar"]{background:#07080F;border-right:1px solid #161A28;}
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span:not(.stCheckbox span),
[data-testid="stSidebar"] .stCaption{color:#8A9AB8!important;font-size:12px!important;}
[data-testid="stSidebar"] h3{color:#E0E8F8!important;font-size:16px!important;font-weight:800!important;}
[data-testid="stSidebar"] hr{border-color:#171D2F!important;}
.stButton>button{border-radius:6px!important;font-weight:700!important;
  border:1px solid #232A40!important;background:#0D1220!important;color:#8A9AB8!important;
  transition:all .15s!important;font-size:12px!important;}
.stButton>button:hover{background:#161E38!important;color:#C0CDE8!important;border-color:#343C58!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#FF6B35,#E84393)!important;
  color:#fff!important;border:none!important;font-size:13px!important;}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{
  background:linear-gradient(135deg,#FF4500,#FF1493,#7B2FFF)!important;
  color:#fff!important;font-weight:800!important;
  box-shadow:0 0 22px rgba(255,69,0,.5)!important;
  animation:pulse-btn 2.5s ease-in-out infinite!important;}
@keyframes pulse-btn{0%,100%{box-shadow:0 0 22px rgba(255,69,0,.5)}50%{box-shadow:0 0 32px rgba(255,20,147,.75)}}
div[data-testid="stMetric"]{background:#090D1C;border:1px solid #1A2038;border-radius:10px;padding:14px;}
div[data-testid="stMetric"] label{color:#4A5870!important;font-size:11px!important;}
div[data-testid="stMetric"] div{color:#E0E8F8!important;font-weight:700!important;}
[data-testid="stSidebar"] input,[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] select{background:#090D1C!important;border:1px solid #1A2038!important;
  color:#C0CDE8!important;border-radius:6px!important;font-size:12px!important;}
.stMainBlockContainer{background:#0A0C14;color:#E0E8F8;}
.stMainBlockContainer p,.stMainBlockContainer span,
.stMainBlockContainer label,.stMainBlockContainer div{color:#B8C8E0;}
.stMainBlockContainer h1,.stMainBlockContainer h2,
.stMainBlockContainer h3,.stMainBlockContainer h4{color:#E0E8F8!important;}
.stMarkdown{color:#B8C8E0!important;}
.stSuccess{background:rgba(52,211,153,.08)!important;border:1px solid rgba(52,211,153,.2)!important;}
.stInfo{background:rgba(99,102,241,.08)!important;border:1px solid rgba(99,102,241,.2)!important;}
.stError{background:rgba(248,113,113,.08)!important;border:1px solid rgba(248,113,113,.2)!important;}
.sec-hdr{font-size:9.5px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;
  color:#3A4868;padding:10px 16px 5px;}
/* 테마 버튼 선택 하이라이트 */
.stButton>button[kind="primary"][data-theme]{
  outline:2px solid var(--c1)!important;}
  @media(max-width:768px){
  [data-testid="stHorizontalBlock"]{flex-direction:column!important;}
  .stMetric{margin-bottom:8px;}
  iframe{min-height:600px!important;}
}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🎓 강사 페이지 빌더 Pro")
    st.caption("수능 강사 랜딩페이지 AI 생성기 v7")
    st.divider()

    # GROQ API Key
    st.markdown('<div class="sec-hdr">🔑 GROQ API KEY</div>', unsafe_allow_html=True)
    api_in = st.text_input("API Key", type="password", value=st.session_state.api_key,
                       placeholder="gsk_...", label_visibility="collapsed")
    if api_in != st.session_state.api_key:
        st.session_state.api_key = api_in
    if st.session_state.api_key:
        st.success("✓ Groq API 키 입력됨 (완전 무료)", icon="✅")
    else:
        st.markdown('<a href="https://console.groq.com" target="_blank" style="font-size:11px;color:#5A6A8A">👆 console.groq.com → API Keys → Create</a>', unsafe_allow_html=True)

    st.markdown('<div class="sec-hdr">🖼 PIXABAY API KEY (배경 이미지)</div>', unsafe_allow_html=True)
    pix_in = st.text_input("Pixabay Key", type="password",
                            value=st.session_state.pixabay_key,
                            placeholder="pixabay.com에서 무료 발급",
                            label_visibility="collapsed")
    if pix_in != st.session_state.pixabay_key:
        st.session_state.pixabay_key = pix_in
        st.session_state.bg_cache = {}
    if st.session_state.pixabay_key:
        st.success("✓ Pixabay 배경 이미지 활성화", icon="🖼")
    else:
        st.markdown('<a href="https://pixabay.com/api/docs/" target="_blank" style="font-size:11px;color:#5A6A8A">👆 pixabay.com → 무료 API 키 발급</a>', unsafe_allow_html=True)

    st.divider()

    # 페이지 목적
    st.markdown('<div class="sec-hdr">📋 페이지 목적</div>', unsafe_allow_html=True)
    pt = st.radio("목적", list(PURPOSE_SECTIONS.keys()),
                  index=list(PURPOSE_SECTIONS.keys()).index(st.session_state.purpose_type),
                  label_visibility="collapsed")
    if pt != st.session_state.purpose_type:
        st.session_state.purpose_type = pt
        st.session_state.active_sections = PURPOSE_SECTIONS[pt].copy()
        st.session_state.custom_copy = None
        st.rerun()
    st.caption(PURPOSE_HINTS[pt])
    st.divider()

    # 컨셉
    st.markdown('<div class="sec-hdr">🎨 페이지 컨셉</div>', unsafe_allow_html=True)

    if st.button("🎲 AI 랜덤 — 매번 완전히 새 디자인!", type="primary", use_container_width=True):
        if not st.session_state.api_key:
            st.warning("API 키를 먼저 입력해주세요")
        else:
            seed = random.choice(RANDOM_SEEDS)
            while len(RANDOM_SEEDS) > 1 and seed == st.session_state.last_seed:
                seed = random.choice(RANDOM_SEEDS)
            st.session_state.last_seed = seed
            with st.spinner(f"'{seed['mood'][:22]}...' 생성 중..."):
                try:
                    r = gen_concept(seed)
                    st.session_state.custom_theme = r
                    st.session_state.concept = "custom"
                    bg = build_bg_url(seed["mood"])
                    st.session_state.bg_photo_url = bg
                    st.success(f"✓ '{r.get('name','새 컨셉')}' 생성!")
                    st.rerun()
                except Exception as e:
                    st.error(f"실패: {e}")

    mood_in = st.text_area("직접 무드 묘사:", height=75, value=st.session_state.ai_mood,
                           placeholder="예: 관중이 가득찬 야구장 밤\n예: 에시드 네온 그린 블랙\n예: 인셉션 다크 에메랄드",
                           label_visibility="visible")
    st.session_state.ai_mood = mood_in

    if st.button("✦ 이 무드로 AI 컨셉 생성", use_container_width=True):
        if not mood_in.strip():
            st.warning("무드를 입력해주세요")
        elif not st.session_state.api_key:
            st.warning("API 키를 먼저 입력해주세요")
        else:
            with st.spinner("AI 컨셉 생성 중..."):
                try:
                    r = gen_concept({"mood":mood_in.strip(),"layout":"auto","font":"auto"})
                    st.session_state.custom_theme = r
                    st.session_state.concept = "custom"
                    bg = build_bg_url(mood_in.strip())
                    st.session_state.bg_photo_url = bg
                    st.session_state.preview_key = st.session_state.get("preview_key", 0) + 1
                    st.session_state.uploaded_bg_b64 = ""
                    st.success(f"✓ '{r.get('name','새 컨셉')}' 생성됨!")
                    st.rerun()
                except Exception as e:
                    st.error(f"실패: {e}")

    # 배경 이미지 업로드
    st.markdown("**🖼 배경 이미지 업로드**")
    st.caption("원하는 이미지를 직접 올리면 히어로 배경으로 사용됩니다")
    uploaded_img = st.file_uploader("배경 이미지", type=["jpg","jpeg","png","webp"],
                                    label_visibility="collapsed", key="bg_uploader")
    
    # 💡 [수정] X 버튼을 눌러 이미지를 삭제했을 때의 처리
    if uploaded_img is None:
        if st.session_state.get("uploaded_bg_b64"):  # 기존에 업로드된 이미지가 있었다면
            st.session_state.uploaded_bg_b64 = ""    # 메모리에서 삭제
            st.session_state.bg_photo_url = ""       # URL도 초기화
            st.rerun()                               # 즉시 화면 새로고침
            
    # 새로운 이미지가 업로드 되었을 때의 처리
    else:
        from PIL import Image
        import io

        img = Image.open(uploaded_img).convert("RGB")

        if img.width > 1920:
            ratio = 1920 / img.width
            img = img.resize((1920, int(img.height * ratio)), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80, optimize=True)
        buf.seek(0)

        b64 = base64.b64encode(buf.read()).decode()
        new_b64 = f"data:image/jpeg;base64,{b64}"
        
        # 기존에 올린 이미지와 다를 때만 업데이트하고 새로고침 (무한 로딩 방지)
        if st.session_state.get("uploaded_bg_b64") != new_b64:
            st.session_state.uploaded_bg_b64 = new_b64
            st.session_state.bg_photo_url = ""
            st.success(f"✓ '{uploaded_img.name}' 업로드됨!")
            st.rerun()

    # 영상 섹션 URL 입력 (video 섹션이 활성화된 경우)
    if "video" in st.session_state.active_sections:
        st.markdown("**🎬 영상 섹션 YouTube URL**")
        st.caption("예: https://www.youtube.com/embed/XXXXXXXXXXX")
        yt_key = "yt_url_input"
        cur_yt = (st.session_state.custom_copy or {}).get("videoUrl","") if st.session_state.custom_copy else ""
        yt_in = st.text_input("YouTube embed URL", value=cur_yt,
                              placeholder="https://www.youtube.com/embed/...",
                              label_visibility="collapsed", key=yt_key)
        if yt_in and yt_in != cur_yt:
            if st.session_state.custom_copy is None:
                st.session_state.custom_copy = {}
            st.session_state.custom_copy["videoUrl"] = yt_in
            st.rerun()

    # 프리셋 테마 버튼
    st.caption("▼ 프리셋 테마 선택:")
    # 신규 테마 먼저
    new_themes = ["stadium","acid","cinematic","floral","inception","violet_pop","brutal","amber"]
    old_themes = ["sakura","fire","ocean","luxury","cosmos","winter","eco"]
    st.caption("✨ 신규 파격 테마")
    cols_n = st.columns(2)
    for i, k in enumerate(new_themes):
        t = THEMES[k]
        with cols_n[i % 2]:
            is_on = st.session_state.concept == k
            if st.button(t["label"], key=f"th_{k}",
                         type="primary" if is_on else "secondary",
                         use_container_width=True):
                st.session_state.concept = k
                st.session_state.custom_theme = None
                st.session_state.bg_photo_url = ""
                st.session_state.preview_key = st.session_state.get("preview_key", 0) + 1
                st.rerun()
    st.caption("기존 테마")
    cols_o = st.columns(2)
    for i, k in enumerate(old_themes):
        t = THEMES[k]
        with cols_o[i % 2]:
            is_on = st.session_state.concept == k
            if st.button(t["label"], key=f"th_{k}",
                         type="primary" if is_on else "secondary",
                         use_container_width=True):
                st.session_state.concept = k
                st.session_state.custom_theme = None
                st.session_state.bg_photo_url = ""
                st.rerun()

    if st.session_state.concept == "custom" and st.session_state.custom_theme:
        ct = st.session_state.custom_theme
        st.success(f"✦ AI 커스텀: {ct.get('name','?')} | {ct.get('heroStyle','?')}", icon="🎨")
        if st.session_state.bg_photo_url:
            st.caption(f"🖼 배경 이미지: {st.session_state.bg_photo_url[:50]}...")

    st.divider()

    # 강사 정보
    st.markdown('<div class="sec-hdr">🎭 카피 어조</div>', unsafe_allow_html=True)
    tone_options = list(COPY_TONES.keys())
    selected_tone = st.radio("어조", tone_options,
        index=tone_options.index(st.session_state.copy_tone),
        label_visibility="collapsed")
    if selected_tone != st.session_state.copy_tone:
        st.session_state.copy_tone = selected_tone
    st.caption(COPY_TONES[st.session_state.copy_tone])
    st.divider()
    st.markdown('<div class="sec-hdr">👤 강사 정보</div>', unsafe_allow_html=True)
    nm = st.text_input("강사명", value=st.session_state.instructor_name,
                       placeholder="강사명", label_visibility="collapsed")
    st.session_state.instructor_name = nm

    sb = st.selectbox("과목", ["영어", "수학", "국어", "사회", "과학"],
                      index=["영어","수학","국어","사회","과학"].index(st.session_state.subject),
                      label_visibility="collapsed")
    st.session_state.subject = sb

    if st.button("🔍 강사 정보 자동 검색", use_container_width=True):
        if not nm:
            st.warning("강사명을 입력해주세요")
        elif not st.session_state.api_key:
            st.warning("API 키를 입력해주세요")
        else:
            with st.spinner(f"{nm} 선생님 정보 검색 중..."):
                try:
                    p = search_instructor(nm, sb)
                    st.session_state.inst_profile = p
                    if p.get("found"):
                        st.success(f"✓ {nm} 선생님 정보 검색 완료!")
                    else:
                        st.info("정보를 찾지 못했습니다.")
                except Exception as e:
                    st.error(f"검색 실패: {e}")
    st.divider()

    # 설정
    st.markdown('<div class="sec-hdr">📝 강의 브랜드명</div>', unsafe_allow_html=True)
    pl = st.text_input("브랜드명", value=st.session_state.purpose_label,
                       placeholder="2026 수능 파이널 완성", label_visibility="collapsed")
    st.session_state.purpose_label = pl
    st.markdown('<div class="sec-hdr">🎯 수강 대상</div>', unsafe_allow_html=True)
    tgt = st.radio("대상", ["고3·N수","고1·2 — 기초 완성"], horizontal=True, label_visibility="collapsed")
    st.session_state.target = tgt
    st.divider()

    # 섹션 ON/OFF
    st.markdown('<div class="sec-hdr">📑 섹션 ON/OFF</div>', unsafe_allow_html=True)
    for sid in PURPOSE_SECTIONS[st.session_state.purpose_type]:
        st.checkbox(SEC_LABELS.get(sid,sid),
                    value=sid in st.session_state.active_sections, key=f"sec_{sid}")

    # 체크박스 위젯 상태 → active_sections 즉시 동기화 (rerun 불필요)
    st.session_state.active_sections = [
        sid for sid in PURPOSE_SECTIONS[st.session_state.purpose_type]
        if st.session_state.get(f"sec_{sid}", False)
    ]

    st.markdown("---")
    csec_on = st.checkbox("✏️ 기타 섹션 추가", value=st.session_state.custom_section_on, key="chk_cs")
    st.session_state.custom_section_on = csec_on
    if csec_on:
        if "custom_section" not in st.session_state.active_sections:
            st.session_state.active_sections.append("custom_section")
        ct_in = st.text_input("섹션 주제", value=st.session_state.custom_section_topic,
                              placeholder="예: 수강평 이벤트, 공지사항",
                              label_visibility="collapsed", key="cs_topic")
        st.session_state.custom_section_topic = ct_in
        if st.button("✦ AI로 섹션 생성", use_container_width=True, key="gen_cs"):
            if not ct_in.strip(): st.warning("주제를 입력해주세요")
            elif not st.session_state.api_key: st.warning("API 키 필요")
            else:
                with st.spinner(f"'{ct_in}' 섹션 생성 중..."):
                    try:
                        r = gen_custom_sec(ct_in)
                        if st.session_state.custom_copy is None:
                            st.session_state.custom_copy = {}
                        st.session_state.custom_copy["custom_section_data"] = r
                        st.success(f"✓ '{r.get('title','섹션')}' 생성됨!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"실패: {e}")
    else:
        if "custom_section" in st.session_state.active_sections:
            st.session_state.active_sections.remove("custom_section")

# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════
ordered = [s for s in PURPOSE_SECTIONS[st.session_state.purpose_type]
           if s in st.session_state.active_sections]
if st.session_state.custom_section_on and "custom_section" not in ordered:
    if st.session_state.custom_copy and st.session_state.custom_copy.get("custom_section_data"):
        ordered.append("custom_section")

final_html = build_html(ordered)
T_now = get_theme()

L, R = st.columns([1, 3], gap="large")

with L:
    st.markdown("### ✍️ AI 문구 생성")
    st.caption(PURPOSE_HINTS[st.session_state.purpose_type])
    ph_map = {
        "신규 커리큘럼": "예: 2026 수능 영어 파이널. 선티 선생님의 KISS Logic 방법론.",
        "이벤트":       "예: 6월 모의고사 대비 특강. 3주 한정 수강료 할인.",
        "기획전":       "예: 2026 영어 기획전. 독해·EBS·어법·파이널 4인 강사 통합.",
    }
    ctx = st.text_area("페이지 맥락", height=100,
                       placeholder=ph_map.get(st.session_state.purpose_type,"맥락 입력"),
                       help="강사 정보 검색 후 생성하면 더 정확한 문구가 나옵니다.")

    if st.button(f"✦ {st.session_state.purpose_type} 문구 AI 생성",
                 type="primary", use_container_width=True):
        if not ctx.strip():
            st.warning("페이지 맥락을 입력해주세요")
        elif not st.session_state.api_key:
            st.warning("API 키를 먼저 입력해주세요")
        else:
            # 활성 섹션 수에 따라 진행 표시
            active = st.session_state.active_sections
            ptype  = st.session_state.purpose_type

            # 목적별로 gen_copy가 커버하는 섹션과 개별 생성할 섹션 구분
            COPY_COVERS = {
                "신규 커리큘럼": ["banner","intro","why","curriculum","target","reviews","faq","cta"],
                "이벤트":       ["banner","event_overview","event_benefits","event_deadline","reviews","cta"],
                "기획전":       ["fest_hero","fest_lineup","fest_benefits","fest_cta"],
            }
            covered     = set(COPY_COVERS.get(ptype, []))
            extra_secs  = [s for s in active if s not in covered and s != "custom_section"]
            total_steps = 1 + len(extra_secs)

            prog   = st.progress(0)
            status = st.empty()

            try:
                # 1단계: gen_copy로 메인 문구 생성 (톤+맥락 반영)
                status.info(f"✍️ 전체 문구 생성 중... (1/{total_steps})")
                r = gen_copy(ctx, ptype,
                             st.session_state.target, st.session_state.purpose_label)
                st.session_state.custom_copy = r
                prog.progress(int(1 / total_steps * 100))

                # 2단계: gen_copy가 커버 못 하는 활성 섹션 개별 생성
                for i, sid in enumerate(extra_secs):
                    label = SEC_LABELS.get(sid, sid)
                    status.info(f"✍️ {label} 섹션 생성 중... ({i+2}/{total_steps})")
                    try:
                        sec_r = gen_section(sid)
                        st.session_state.custom_copy.update(sec_r)
                    except Exception:
                        pass
                    prog.progress(int((i + 2) / total_steps * 100))

                prog.progress(100)
                status.empty()
                prog.empty()
                st.session_state.preview_key = st.session_state.get("preview_key", 0) + 1
                import copy, datetime
                snapshot = {
                    "time": datetime.datetime.now().strftime("%H:%M"),
                    "tone": st.session_state.copy_tone,
                    "concept": st.session_state.concept,
                    "copy": copy.deepcopy(st.session_state.custom_copy),
                    "label": st.session_state.purpose_label[:10],
                }
                hist = st.session_state.history or []
                hist.insert(0, snapshot)
                st.session_state.history = hist[:5]
                st.success(f"✓ 전체 {len(active)}개 섹션 문구 생성 완료!")

            except Exception as e:
                prog.empty()
                status.empty()
                st.error(f"생성 실패: {e}")

    if st.session_state.custom_copy:
        st.success("✓ AI 문구 적용됨", icon="✅")
        if st.button("✕ 문구 초기화", use_container_width=True):
            st.session_state.custom_copy = None
            st.rerun()

    st.divider()

    st.markdown("### 🎲 섹션별 문구 재생성")
    st.caption("클릭 시 해당 섹션 문구만 새롭게 교체됩니다")

    SEC_SHORT = {
        'banner':'배너', 'intro':'소개', 'why':'이유', 'curriculum':'커리큘럼',
        'target':'대상', 'reviews':'수강평', 'faq':'FAQ', 'cta':'CTA',
        'video':'영상', 'before_after':'전/후', 'method':'학습법', 'package':'구성',
        'event_overview':'개요', 'event_benefits':'혜택', 'event_deadline':'마감',
        'fest_hero':'히어로', 'fest_lineup':'라인업', 'fest_benefits':'혜택', 'fest_cta':'CTA',
    }
    regen_secs = [s for s in ordered if s in SEC_LABELS and s != 'custom_section']
    if regen_secs and st.session_state.api_key:
        for row_start in range(0, len(regen_secs), 4):
            chunk = regen_secs[row_start:row_start+4]
            cols_r = st.columns(4)
            for i, sid in enumerate(chunk):
                label = SEC_SHORT.get(sid, sid)
                with cols_r[i]:
                    if st.button(f"↺ {label}", key=f"regen_{sid}",
                                 use_container_width=True):
                        with st.spinner(f"{label} 재생성..."):
                            try:
                                r = gen_section(sid)
                                if st.session_state.custom_copy is None:
                                    st.session_state.custom_copy = {}
                                st.session_state.custom_copy.update(r)
                                st.session_state.preview_key = st.session_state.get("preview_key", 0) + 1
                                st.rerun()
                            except Exception as e:
                                st.error(f"실패: {e}")
    elif not st.session_state.api_key:
        st.caption("API 키를 입력하면 활성화됩니다.")
    st.divider()

    # 문구 직접 편집 — 섹션별 개별 필드 즉시 반영
    st.markdown("### ✏️ 문구 직접 편집")
    if st.session_state.custom_copy:
        cp = st.session_state.custom_copy

        # 편집 가능한 섹션 목록 동적 구성
        edit_sections = []
        pt = st.session_state.purpose_type
        if pt == "신규 커리큘럼":
            edit_sections = [
                ("🏠 배너", [
                    ("text_input","메인 제목","bannerTitle"),
                    ("text_area","리드 문구","bannerLead"),
                    ("text_input","버튼 텍스트","ctaCopy"),
                    ("text_input","브랜드 문구","brandTagline"),
                ]),
                ("👤 강사 소개", [
                    ("text_input","소개 제목","introTitle"),
                    ("text_area","소개 본문","introDesc"),
                    ("text_input","한줄 약력","introBio"),
                ]),
                ("💡 수강 이유", [
                    ("text_input","섹션 제목","whyTitle"),
                    ("text_input","서브 제목","whySub"),
                ]),
                ("📚 커리큘럼", [
                    ("text_input","섹션 제목","curriculumTitle"),
                    ("text_input","서브 제목","curriculumSub"),
                ]),
                ("📣 CTA", [
                    ("text_area","CTA 제목","ctaTitle"),
                    ("text_input","서브문구","ctaSub"),
                    ("text_input","버튼 텍스트","ctaCopy"),
                ]),
            ]
        elif pt == "이벤트":
            edit_sections = [
                ("🏠 배너", [
                    ("text_input","메인 제목","bannerTitle"),
                    ("text_area","리드 문구","bannerLead"),
                ]),
                ("📅 이벤트 개요", [
                    ("text_input","이벤트 제목","eventTitle"),
                    ("text_area","이벤트 설명","eventDesc"),
                ]),
                ("⏰ 마감 안내", [
                    ("text_input","마감 제목","deadlineTitle"),
                    ("text_area","마감 메시지","deadlineMsg"),
                ]),
                ("📣 CTA", [
                    ("text_input","버튼 텍스트","ctaCopy"),
                ]),
            ]
        elif pt == "기획전":
            edit_sections = [
                ("🏆 히어로", [
                    ("text_input","히어로 제목","festHeroTitle"),
                    ("text_input","서브 카피","festHeroCopy"),
                    ("text_area","설명","festHeroSub"),
                ]),
                ("📣 기획전 CTA", [
                    ("text_input","CTA 제목","festCtaTitle"),
                    ("text_area","서브문구","festCtaSub"),
                ]),
            ]

        for sec_label, fields in edit_sections:
            with st.expander(sec_label, expanded=False):
                changed = {}
                for ftype, flabel, fkey in fields:
                    cur_val = cp.get(fkey,"")
                    wkey = f"ed_{fkey}"
                    if ftype == "text_area":
                        val = st.text_area(flabel, value=cur_val, height=72, key=f"ed_{sec_label}_{fkey}")
                    else:
                        val = st.text_input(flabel, value=cur_val, key=f"ed_{sec_label}_{fkey}")
                    if val != cur_val:
                        changed[fkey] = val
                if changed:
                    if st.button("✓ 적용", key=f"apply_{sec_label}_btn"):
                        st.session_state.custom_copy.update(changed)
                        st.rerun()
    else:
        st.caption("💡 AI로 문구를 먼저 생성하면 여기서 항목별로 수정할 수 있습니다.")

    st.divider()

    # HTML 내보내기
    if st.session_state.history:
        st.markdown("### 🕐 생성 히스토리")
        st.caption("클릭하면 해당 버전으로 복원됩니다")
        for i, snap in enumerate(st.session_state.history):
            col_h, col_btn = st.columns([3, 1])
            with col_h:
                st.markdown(f"**{snap['time']}** · {snap['tone']} · `{snap['label']}`")
            with col_btn:
                if st.button("복원", key=f"hist_{i}", use_container_width=True):
                    st.session_state.custom_copy = snap["copy"]
                    st.session_state.copy_tone   = snap["tone"]
                    st.session_state.concept     = snap["concept"]
                    st.session_state.preview_key = st.session_state.get("preview_key", 0) + 1
                    st.rerun()
        st.divider()
    st.markdown("### 📥 HTML 내보내기")
    cn = (st.session_state.custom_theme.get("name","custom")
          if st.session_state.concept=="custom" and st.session_state.custom_theme
          else st.session_state.concept)
    st.download_button(
        "📥 HTML 파일 다운로드",
        data=final_html.encode("utf-8"),
        file_name=f"{st.session_state.instructor_name or 'page'}_{st.session_state.subject}_{cn}.html",
        mime="text/html",
        use_container_width=True,
    )

    # ── 실무 활용 팁 ──────────────────────────────
    with st.expander("💡 실무 활용 & 추가 기능 안내", expanded=False):
        st.markdown("""
**지금 바로 쓸 수 있는 팁**

🔗 **URL 배포**: HTML 다운로드 → Notion / Carrd / GitHub Pages에 업로드하면 바로 공유 가능

📱 **카카오톡 공유**: 대성마이맥 수강 신청 링크를 `href="#"` 부분에 실제 URL로 교체

🖼 **배경 이미지 교체**: '배경 이미지 업로드' 기능으로 실제 강의 사진 사용 권장

✏️ **문구 직접 편집**: 배너·소개 섹션은 아래 '문구 직접 편집' 패널에서 수동 수정 가능

---

**추가하면 좋을 기능 (요청 시 구현 가능)**

| 기능 | 설명 |
|------|------|
| 📊 A/B 테스트 모드 | 2개 버전 문구를 동시 생성해 비교 |
| 🌐 OG 태그 자동 생성 | SNS 공유 시 미리보기 이미지·제목 자동 세팅 |
| 📅 마감일 직접 입력 | 카운트다운 타이머 날짜 수동 설정 |
| 🎞 영상 히어로 | 배경을 MP4/YouTube 영상으로 교체 |
| 🔔 네이버폼 연동 | 수강신청 폼을 CTA 버튼에 직접 임베드 |
| 💬 카카오 채널 위젯 | 우하단 플로팅 카카오 문의 버튼 삽입 |
| 📈 Google Analytics | UA/GA4 트래킹 코드 자동 삽입 |
""")


with R:
    st.markdown("### 👁 실시간 미리보기")

    td = (st.session_state.custom_theme.get("name", "AI 커스텀")
          if st.session_state.concept == "custom" and st.session_state.custom_theme
          else THEMES.get(st.session_state.concept, {}).get("label", ""))

    col_info1, col_info2, col_info3, col_ref = st.columns([2, 2, 2, 1])
    with col_info1: st.metric("컨셉", td)
    with col_info2: st.metric("히어로", T_now.get("heroStyle", "—"))
    with col_info3: st.metric("섹션 수", len(ordered))
    with col_ref:
        if st.button("🔄", key="refresh_preview", help="미리보기 새로고침"):
            st.session_state.preview_key = st.session_state.get("preview_key", 0) + 1
            st.rerun()

    if "preview_large" not in st.session_state:
        st.session_state.preview_large = False

    if st.button("🔍 미리보기 크게/작게 전환", use_container_width=True):
        st.session_state.preview_large = not st.session_state.preview_large
        st.rerun()

    preview_height = 1400 if st.session_state.preview_large else 700
    import streamlit.components.v1 as components
    components.html(final_html, height=preview_height, scrolling=True)
