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
    "metaphor": "",
    "instructor_name": "", "subject": "영어",
    "purpose_label": "2026 수능 파이널 완성",
    "purpose_type": "신규 커리큘럼", "target": "고3·N수",
    "custom_copy": None, "bg_photo_url": "",
    "active_sections": ["banner","intro","why","curriculum","cta"],
    "ai_mood": "", "inst_profile": None, "last_seed": None,
    "custom_section_on": False, "custom_section_topic": "",
    "uploaded_bg_b64": "",
    "pixabay_key": "", "bg_cache": {}, "preview_key": 0,
    "copy_tone": "✨ 압도적·카리스마",  # <--- 이 부분이 수정되었습니다!
    "history": [],
    "course_info": "",
    "textbook_info": "",
    "course_copy": None,
    "textbook_copy": None,
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
    "✨ 압도적·카리스마": "어조: 절대적인 확신과 카리스마. 수험생의 현실 안일함을 차가운 팩트로 찌름. 문장은 짧고 압도적이어야 함. 예) '아직도 감으로 공부해?', '남은 시간이 없어요'",
    "🤝 철학적·감동": "어조: 선배 같은 따뜻함과 깊은 철학. 학생의 본질적인 고민을 어루만지고 감동을 주는 방식. 상황 묘사보다 감정적 울림 중심.",
    "💎 프리미엄·신뢰": "어조: 고급 브랜드처럼 절제된 톤. 수식어를 최소화하고 오직 압도적인 결과와 사실로 승부. 숫자를 세련되게 활용.",
    "😎 힙·MZ": "어조: 트렌디하고 감각적. 설명하지 않고 결과와 이미지로만 멋을 내는 방식. 예) '말해 뭐해? 결과가 증명해'",
    "📖 논리적·분석": "어조: 전문적이고 데이터 중심. 출제 패턴, 숫자, 논리적 근거로 차분하게 설득.",
    "🔥 독설·팩폭": "어조: 피도 눈물도 없는 차가운 독설. 감정적 위로 절대 금지. '이래서 네가 안 돼' 식의 차가운 논리로 정신 차리게 함.",
    "🔮 광기·구원": "어조: 학생을 홀리는 듯한 극단적이고 맹신적인 문체. 이 강의만이 유일한 구원이라는 오만함과 확신. 감탄문과 극단적인 단어 사용."
}
GROQ_MODELS = [
    "llama-3.3-70b-versatile",          # 메인 (기존 유지)
    "meta-llama/llama-4-scout-17b-16e-instruct",  # Llama 4 Scout
    "qwen/qwen3-32b",                   # Qwen 3 32B
    "llama-3.1-8b-instant",             # 경량 빠른 모델 (gemma2-9b-it 후계)
]

FEW_SHOT_EXAMPLES = """
=== 🏆 인간이 직접 쓴 것 같은 문구의 특징 ===
좋은 카피는 다음 3가지를 동시에 충족한다:
1. 수험생의 지금 상황을 정확히 묘사 (추상적 희망 금지)
2. 이 강의가 왜 지금 필요한지 논리적 근거 제시
3. 강좌명·메타포가 문장 안에 자연스럽게 녹아있음

[실제 수험생이 공감하는 문장 패턴]
- "지문은 읽히는데 답은 모르겠다. 그게 네 현실이다."
- "3월에 방향을 잘못 잡으면 11월에 후회한다."
- "감으로 맞히는 건 수능장에서 통하지 않는다. 진또배기는 구조로 읽는다."
- "공부는 하는데 성적이 안 오른다면, 방향이 틀린 것이다."
- "국어 지문에는 출제자가 만든 구조가 있다. 그 구조를 보는 눈을 만드는 것이 진또배기의 시작이다."

[성의없는 AI 문구 vs 인간 문구 비교]
❌ "체계적인 학습으로 성적을 올리세요" (→ 아무 의미 없음)
✅ "3월에 구조 잡고, 6월에 패턴 읽고, 수능장에서 답을 본다. 진또배기의 순서다."

❌ "최고의 강사와 함께라면 가능합니다" (→ 근거 없는 희망)
✅ "국어 지문은 처음부터 끝까지 읽지 않아도 된다. 어디를 읽어야 하는지 아는 것이 실력이다."

❌ "수강생들이 만족하는 강의입니다" (→ 증명 불가)
✅ "지문 구조가 보이기 시작하면, 시험장에서 처음으로 시간이 남는 경험을 한다."

=== ❌ 절대 쓰지 말 것 — AI 클리셰 목록 ===
아래 표현은 진부하고 AI스럽게 들립니다. 이것이 떠오르면 반드시 뒤집어서 다시 쓰세요.

❌ "체계적인 학습 시스템"
✅ 대신: "3월에 뭐부터 해야 할지 감이 잡히지 않는다면, 이 강의가 길을 만들어 드립니다"

❌ "최고의 강사진이 함께합니다"  
✅ 대신: "[강사명]만의 방식으로 지문이 처음으로 '읽히는' 경험을 하게 됩니다"

❌ "합리적인 가격으로 성적을 올리세요"
✅ 대신: "6월 모평 전, 딱 한 번의 선택이 남았습니다"

❌ "체계적이고 효율적인 커리큘럼"
✅ 대신: "개념 → 기출 → 실전. 이 순서대로 하면 6월이 다릅니다"

❌ "실력 향상을 도와드립니다"
✅ 대신: "지금 이 강의를 듣는 학생은 수능장에서 '아, 이거다' 하는 순간이 옵니다"

❌ "많은 수험생들이 선택했습니다"
✅ 대신: "같은 지문, 같은 시간. 근데 왜 어떤 학생만 답이 보일까요?"

=== 페이지 맥락별 문구 방향 예시 ===
[6월 모평 대비 페이지라면]
- 배너: "6월이 판가름 난다. 지금이 마지막 기회다."
- 소개: "6월 모평 직전, 이 수업이 필요한 이유가 있습니다."
- 수강이유: "모평 2주 전에 할 수 있는 것과 없는 것이 있습니다."
- 커리큘럼: "모평까지 남은 시간에 맞게 설계된 4단계"
- CTA: "6월 모평 전 마지막 기회, 지금 신청하세요"

[3월 개강 커리큘럼이라면]
- 배너: "3월 첫 선택이 수능 결과를 만든다"
- 소개: "아직 늦지 않았습니다. 3월부터 시작하면 됩니다."
- 수강이유: "수능까지 9개월, 지금 방향을 잡으면 다릅니다"
- CTA: "오늘이 가장 빠른 시작입니다"

[파이널/수능 직전이라면]
- 배너: "D-30. 이제 더 추가할 게 아니라 버릴 때입니다"
- 소개: "수능 직전, 딱 필요한 것만 담았습니다"
- CTA: "수능 전 마지막 강의, 지금이 마지막입니다"

=== AI스러운 표현 절대 금지 목록 ===
아래 패턴이 나오면 즉시 다시 써라.

❌ "아직도 ~하고 있나요?" → ✅ 강좌명 + 짧은 선언
❌ "~의 비밀을 공개합니다" → ✅ "~으로 끝낸다" / "~이 달라진다"
❌ "함께라면 가능합니다" → ✅ 구체적 결과 수치나 상황
❌ "지금 바로 시작하세요" (단독) → ✅ 왜 지금인지 이유 포함
❌ "수능까지 함께" → ✅ 남은 기간이나 시험명 직접 언급
❌ "체계적으로 준비" → ✅ 구체적 방법론명 사용
❌ "실력이 달라집니다" → ✅ "3주 차부터 지문 구조가 보인다"
❌ "최고의 강의" → ✅ 강사 시그니처 메서드명
❌ "성적을 올리세요" → ✅ "모평에서 한 등급 오른다"
❌ "열심히 하면" → ✅ "이 순서대로 하면"

=== 실제로 통하는 문구 패턴 ===
[bannerTitle — 강좌명이 반드시 들어가는 형태]
- 진또배기
- 진또배기 — 국어의 본질
- 뉴런으로 끝낸다
- KISS Logic, 단 하나면 됩니다

[bannerLead — 학생 상황 직격]
- 지문은 읽히는데 답은 모르겠다. 그게 지금 너의 상황이다.
- 국어 3등급, 공부는 했는데 왜 안 오르는지 모르겠다면.
- 감으로 맞추는 건 수능장에서 통하지 않는다.

[whyReasons 설명 — 뼈 때리는 방식]
- "기출을 풀었지만 '왜 틀렸는지'를 모른다면, 다음 시험도 같은 유형에서 틀린다. 진또배기는 답보다 원리를 먼저 가르친다."
- "국어 지문은 감으로 읽는 게 아니다. 구조가 있다. 이 구조를 보는 눈을 3주 안에 만들어 드린다."
""" + """

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
=== 강좌명·컨셉 워드플레이 필수 규칙 ===
강좌명이나 페이지 맥락에서 반드시 단어 유희를 찾아내어 문구에 녹여라.

[영문 강좌명 워드플레이 예시]
- "KEY STEP" → bannerTitle: "1등급을 향한 열쇠, KEY STEP" / brandTagline: "한 스텝(STEP) 더, 1등급의 문이 열립니다(KEY)"
- "KISSAVE" → bannerTitle: "KISSAVE — 너의 점수를 구한다" / brandTagline: "이제 KISS가 너의 점수를 세이브(SAVE)한다"
- "KISSCHEMA" → "스키마(SCHEMA)처럼 구조가 잡힌다" / "머릿속 영어 회로가 바뀝니다"
- "뉴런" → "이제 뇌가 다르게 연결됩니다" / "뉴런이 바뀌면 점수가 바뀐다"
- "인셉션" → "머릿속 깊이 심어지는 국어 원리" / "꿈꾸듯 읽히기 시작합니다"
- "R'gorithm" → "독해에도 알고리즘이 있다" / "논리 회로가 켜지는 순간"
- "All Of KICE" → "수능 출제진의 모든 것을 담았다" / "KICE가 만든 모든 것, 우리가 먼저 분석했다"
- "Starting Block" → "출발선이 달라지면 도착점이 달라진다"
- "KICE Anatomy" → "수능을 해부한다"

[한국어 강좌명 워드플레이 예시]
- "파노라마" → "국어가 파노라마처럼 펼쳐집니다" / "전체가 한눈에 보이는 순간"
- "세젤쉬" → "세상에서 제일 쉬운 수학이 됩니다"
- "미친개념" → "이 정도면 미쳤다고 할 수밖에 없는 개념 강의"

규칙:
1. bannerTitle과 brandTagline에는 강좌명의 의미·발음·약자를 활용한 워드플레이를 반드시 1개 이상 포함
2. introDesc, whyReasons, ctaSub에서도 강좌명과 자연스럽게 연결된 표현 사용
3. 영문 강좌명은 한국어 뜻/발음도 함께 활용 (KEY=열쇠, SAVE=저장/구원, KISS=간결, STEP=단계 등)
4. 억지스러운 워드플레이 금지 — 읽었을 때 "아, 맞다!" 하고 자연스럽게 느껴져야 함
5. 강좌명을 모르는 독자도 이해할 수 있게 뜻을 문구 안에 녹여야 함
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

THEME_PREVIEW_COLORS = {
    "acid":       ["#030703", "#AAFF00", "#CCFF44"],
    "cinematic":  ["#050005", "#FF1744", "#FF5252"],
    "stadium":    ["#020008", "#FF2244", "#FF6688"],
    "inception":  ["#010C06", "#2DB87C", "#4ECFA0"],
    "amber":      ["#080400", "#F59E0B", "#FCD34D"],
    "brutal":     ["#F5F5F0", "#1A1A1A", "#444444"],
    "violet_pop": ["#FAFAFF", "#7C3AED", "#9F67FF"],
    "floral":     ["#FFFAF8", "#E8386D", "#F472A8"],
    "cosmos":     ["#030712", "#7C3AED", "#06B6D4"],
    "fire":       ["#0D0705", "#FF4500", "#FF8C00"],
    "luxury":     ["#0C0B09", "#C8975A", "#D4AF72"],
    "ocean":      ["#F0F9FF", "#0EA5E9", "#38BDF8"],
    "sakura":     ["#FBF6F4", "#B5304A", "#E89BB5"],
    "winter":     ["#F8FAFF", "#1E40AF", "#3B82F6"],
    "eco":        ["#F0FDF4", "#059669", "#34D399"],
}

PURPOSE_SECTIONS = {
    "신규 커리큘럼": ["banner","intro","video","grade_stats","before_after","instructor_philosophy","method","why","curriculum","course_intro","textbook_sale","target","package","reviews","faq","cta"],
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
    "banner":"🏠 메인 배너","intro":"📖 강좌 핵심 소개","why":"💡 필요한 이유",
    "curriculum":"📚 커리큘럼","target":"🎯 수강 대상","reviews":"⭐ 수강평",
    "faq":"❓ FAQ","cta":"📣 수강신청",
    "video":"🎬 영상 미리보기","before_after":"🔄 수강 전/후","method":"🧪 학습법 시각화","package":"📦 구성 안내",
    "grade_stats":"📊 등급 변화 성과",
    "event_overview":"📅 이벤트 개요","event_benefits":"🎁 이벤트 혜택",
    "event_deadline":"⏰ 마감 안내",
    "fest_hero":"🏆 기획전 히어로","fest_lineup":"👥 강사 라인업",
    "fest_benefits":"🎁 기획전 혜택","fest_cta":"📣 기획전 CTA",
    "custom_section":"✏️ 기타 섹션",
    "course_intro": "📖 강좌 소개",        # ← 추가
    "textbook_sale": "📦 교재 소개·판매",   # ← 추가
    "instructor_philosophy": "💭 강사 철학", # ← 추가
    "season_roadmap": "🗓 시즌 로드맵",     # ← 추가
}
RANDOM_SEEDS = [
    # ── K-컬처·팝아트 ──
    {"mood": "K팝 콘서트 무대 홀로그램 팬들 형광봉 핑크 블루", "layout": "billboard", "font": "display", "particle": "stars"},
    {"mood": "웹툰 스타일 만화 그라디언트 벡터 컬러풀 팝", "layout": "brutal", "font": "display", "particle": "none"},
    {"mood": "뉴트로 1990년대 한국 오락실 픽셀 레트로 네온", "layout": "brutal", "font": "mono", "particle": "none"},
    {"mood": "한국 드라마 세트장 감성 조명 인물 드라마틱", "layout": "editorial", "font": "serif", "particle": "none"},
 
    # ── 프리미엄 학습 공간 ──
    {"mood": "조용한 독서실 새벽 3시 스탠드 불빛 연필 소리", "layout": "minimal", "font": "serif", "particle": "none"},
    {"mood": "명문대 캠퍼스 가을 은행잎 도서관 클래식", "layout": "editorial", "font": "serif", "particle": "leaves"},
    {"mood": "하버드 법대 강의실 오크 목재 책상 가죽 빈티지", "layout": "editorial", "font": "serif", "particle": "none"},
    {"mood": "스탠퍼드 컴퓨터 사이언스 화이트 미니멀 실리콘밸리", "layout": "minimal", "font": "sans", "particle": "none"},
 
    # ── 추상·그래픽 ──
    {"mood": "라우터 데이터 흐름 파란 빛 네트워크 선 추상", "layout": "immersive", "font": "mono", "particle": "stars"},
    {"mood": "DNA 이중나선 생명과학 초록 파랑 추상 미래", "layout": "immersive", "font": "sans", "particle": "none"},
    {"mood": "수학 공식 칠판 분필 흰색 심플 클래식", "layout": "minimal", "font": "mono", "particle": "none"},
    {"mood": "뇌 신경망 시냅스 빛 연결 파란 보라 추상", "layout": "immersive", "font": "sans", "particle": "stars"},
    {"mood": "무한 우주 거울 반사 황금 프랙탈 만다라", "layout": "editorial", "font": "serif", "particle": "gold"},
 
    # ── 계절·시간대 극적 장면 ──
    {"mood": "장마 빗소리 창문 물방울 흘러내림 회색 고요", "layout": "minimal", "font": "serif", "particle": "none"},
    {"mood": "봄 새벽 안개 속 은행나무 한 그루 여백", "layout": "minimal", "font": "serif", "particle": "none"},
    {"mood": "가을 한강 노을 다리 실루엣 오렌지 서울", "layout": "editorial", "font": "serif", "particle": "gold"},
    {"mood": "한여름 밤 열섬 서울 옥상 선풍기 반짝이는 별", "layout": "immersive", "font": "sans", "particle": "stars"},
    {"mood": "폭설 내리는 수능 시험장 앞 수험생 떨리는 아침", "layout": "minimal", "font": "serif", "particle": "snow"},
 
    # ── 극한 대비 미학 ──
    {"mood": "피어나는 꽃 vs 콘크리트 벽 충돌 생명력 도시", "layout": "brutal", "font": "display", "particle": "petals"},
    {"mood": "어둠 속 단 하나의 촛불 손 따뜻함 집중", "layout": "minimal", "font": "serif", "particle": "embers"},
    {"mood": "낡은 교과서 위 형광펜 밑줄 클로즈업 노스탤지어", "layout": "minimal", "font": "serif", "particle": "none"},
    {"mood": "CMYK 원색 팝아트 할리우드 빈티지 포스터", "layout": "billboard", "font": "display", "particle": "none"},
 
    # ── 동아시아 미학 ──
    {"mood": "교토 대나무 숲 초록 새벽 빛 고요 선", "layout": "minimal", "font": "serif", "particle": "leaves"},
    {"mood": "홍콩 야시장 홍등 빨간 연기 소란 따뜻함", "layout": "brutal", "font": "display", "particle": "embers"},
    {"mood": "서울 경복궁 달밤 전통 기와 파란 하늘 고요", "layout": "editorial", "font": "serif", "particle": "none"},
    {"mood": "상하이 와이탄 야경 황포강 반사 골드 모더니즘", "layout": "editorial", "font": "serif", "particle": "gold"},

    # ── 스포츠 ──────────────────────────────────────
    {"mood":"관중이 가득찬 야구장 밤 전광판 붉은빛 함성","layout":"brutal","font":"display","particle":"none"},
    {"mood":"축구 경기장 잔디 조명 초록 밤 전광판 함성","layout":"brutal","font":"display","particle":"none"},
    {"mood":"농구 코트 나무 바닥 스포트라이트 NBA 에너지","layout":"brutal","font":"display","particle":"none"},
    {"mood":"복싱 링 위 스포트라이트 땀 격투 집중","layout":"brutal","font":"display","particle":"none"},
    {"mood":"수영장 물결 파란 레인 선수 출발대 새벽","layout":"immersive","font":"display","particle":"none"},
    {"mood":"F1 레이싱 서킷 타이어 연기 아드레날린 스피드","layout":"brutal","font":"display","particle":"embers"},
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
    # ── 자연 & 계절의 압도적 풍경 ──────────────────────────
    {"mood":"심해 1000m 심해어 발광 코발트 블루 극도의 고요","layout":"immersive","font":"serif","particle":"none"},
    {"mood":"열대우림 아마존 정글 짙은 녹색 안개 습기 생명력","layout":"organic","font":"sans","particle":"leaves"},
    {"mood":"북유럽 숲 속 오두막 아침 안개 피톤치드 에메랄드","layout":"organic","font":"serif","particle":"leaves"},
    {"mood":"북극 빙하 크레바스 창백한 푸른빛 맹렬한 추위","layout":"brutal","font":"display","particle":"snow"},
    {"mood":"사막 붉은 모래언덕 타는 듯한 태양 황홀한 일몰","layout":"editorial","font":"serif","particle":"gold"},
    {"mood":"해저 동굴 부서지는 햇살 아쿠아마린 평화로움","layout":"immersive","font":"sans","particle":"none"},
    {"mood":"봄바람 흩날리는 벚꽃잎 연분홍빛 설렘 따뜻함","layout":"editorial","font":"serif","particle":"petals"},
    # ── 우주·SF ──────────────────────────────────────
    {"mood":"우주 정거장 내부 홀로그램 코발트 블루 테크","layout":"immersive","font":"mono","particle":"stars"},
    {"mood":"블랙홀 이벤트 호라이즌 빛 왜곡 심우주","layout":"immersive","font":"mono","particle":"stars"},
    {"mood":"화성 표면 붉은 사막 탐사 미래","layout":"editorial","font":"mono","particle":"none"},
    {"mood":"AI 회로 기판 초록 데이터 흐름 매트릭스","layout":"brutal","font":"mono","particle":"none"},
    {"mood":"양자 컴퓨터 파란 빛 구체 에너지 추상","layout":"immersive","font":"mono","particle":"stars"},
    {"mood":"우주 웜홀 진입 순간 시공간 왜곡 보라빛 빛줄기","layout":"immersive","font":"sans","particle":"stars"},
    {"mood":"하이테크 연구소 클린룸 무균실 하얀 불빛 미래","layout":"minimal","font":"mono","particle":"none"},
    {"mood":"초현실주의 마그리트 사막 위 떠있는 구체 기묘함","layout":"editorial","font":"serif","particle":"none"},
    # ── 예술·문화 ────────────────────────────────────
    {"mood":"고대 이집트 황금 신전 사막 모래 오벨리스크","layout":"editorial","font":"serif","particle":"gold"},
    {"mood":"빈티지 옥스퍼드 도서관 가죽 책 양피지 세피아","layout":"editorial","font":"serif","particle":"none"},
    {"mood":"19세기 파리 아방가르드 예술 포스터 타이포","layout":"brutal","font":"display","particle":"none"},
    {"mood":"재즈 바 스모키 앰버 조명 클래식 무드","layout":"editorial","font":"serif","particle":"gold"},
    {"mood":"록 콘서트 무대 스포트라이트 연기 에너지","layout":"brutal","font":"display","particle":"embers"},
    {"mood":"발레 무용수 무대 스포트라이트 우아 흰색","layout":"editorial","font":"serif","particle":"none"},
    {"mood":"일본 전통 정원 벚꽃 고요 선 미학","layout":"minimal","font":"serif","particle":"petals"},
    {"mood":"바이킹 북유럽 회색 석조 웅장","layout":"editorial","font":"display","particle":"snow"},
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
    # ── 럭셔리 & 감성 & 건축 ────────────────────────────
    {"mood":"대리석 조각상 박물관 순백색 우아함 프리미엄","layout":"editorial","font":"serif","particle":"none"},
    {"mood":"따뜻한 위스키 바 재즈 앰버 조명 얼음 클래식","layout":"editorial","font":"serif","particle":"gold"},
    {"mood":"파리 샹젤리제 거리 에펠탑 야경 낭만적인 골드","layout":"editorial","font":"serif","particle":"gold"},
    {"mood":"뉴욕 월스트리트 빌딩숲 차가운 유리 반사 성공","layout":"billboard","font":"sans","particle":"none"},
    {"mood":"일본 쿄토 료칸 다도 다다미방 차분한 젠(Zen) 스타일","layout":"minimal","font":"serif","particle":"leaves"},
    {"mood":"한국 전통 수묵화 흑백 여백의 미 먹 번짐 붓글씨","layout":"minimal","font":"serif","particle":"none"},
    {"mood":"슈퍼카 엔진룸 탄소섬유 강렬한 레드 크롬 테크","layout":"immersive","font":"display","particle":"none"},
    # ── 디자인 트렌드 & 파격 실험 ───────────────────────────────
    {"mood":"베이퍼웨이브 80년대 레트로 네온 핑크 시안 그리드","layout":"brutal","font":"display","particle":"stars"},
    {"mood":"Y2K 세기말 감성 메탈릭 실버 홀로그램 글리치","layout":"immersive","font":"sans","particle":"stars"},
    {"mood":"글래스모피즘 반투명 유리 다채로운 파스텔 오로라","layout":"modern","font":"sans","particle":"snow"},
    {"mood":"애시드 테크노 레이브 형광 노랑 핫핑크 사이키델릭","layout":"brutal","font":"display","particle":"none"},
    {"mood":"브루탈리즘 거친 콘크리트 압도적인 검은색 타이포그래피","layout":"brutal","font":"sans","particle":"none"},
    {"mood":"사이버네틱 매트릭스 디지털 비 해킹 초록 코드","layout":"brutal","font":"mono","particle":"none"},
    {"mood":"미니멀리즘 순백색 캔버스 단 하나의 선 숨막히는 여백","layout":"minimal","font":"serif","particle":"none"},
    {"mood":"다크 아카데미아 빅토리안 고딕 도서관 촛불 은은함","layout":"editorial","font":"serif","particle":"none"},
    # ── 최신 트렌드 & 하이엔드 무드 (세련됨 극대화) ──
    {"mood": "애플 스타일 다크 미니멀리즘 심해의 고요함 순수 블랙과 티타늄 실버", "layout": "minimal", "font": "sans", "particle": "none"},
    {"mood": "Vercel 스타일 개발자 감성 다크 테크 간결한 선과 네온 블루 포인트", "layout": "modern", "font": "mono", "particle": "none"},
    {"mood": "프리미엄 스킨케어 브랜드 베이지 톤 오가닉 여백의 미 부드러움", "layout": "editorial", "font": "serif", "particle": "none"},
    {"mood": "하이엔드 패션 매거진 흑백 대비 강렬한 붉은색 타이포그래피 포인트", "layout": "brutal", "font": "display", "particle": "none"},
    {"mood": "우주 탐사선 내부 창백한 푸른빛과 매트한 딥 그레이 사이파이", "layout": "immersive", "font": "sans", "particle": "stars"},
    {"mood": "새벽 5시 안개 낀 서울 도심 차가운 남색과 가로등 불빛", "layout": "minimal", "font": "sans", "particle": "none"},
    {"mood": "홀로그램 오로라 투명한 유리 질감 파스텔 보라와 에메랄드", "layout": "modern", "font": "sans", "particle": "none"},
    {"mood": "스트릿 브랜드 룩북 힙합 거친 콘크리트 질감과 쨍한 오렌지", "layout": "brutal", "font": "display", "particle": "none"},
    {"mood": "초현실주의 사막 한가운데 놓인 거울 앰버와 골드 웜톤", "layout": "editorial", "font": "serif", "particle": "gold"},
    {"mood": "Y2K 레트로 퓨처리즘 메탈릭 실버와 사이버틱 핑크", "layout": "immersive", "font": "display", "particle": "stars"},
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
    import re

    # 허용 문자 패턴
    allowed_pattern = r'[^\u3131-\u3163\uAC00-\uD7A3a-zA-Z0-9\s\.\,\!\?\'\"\%\[\]\(\)\-\<\>~·/&+]'
    cleaned = re.sub(allowed_pattern, '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)

    # ✅ 추가: AI가 자주 생성하는 비한국어 외래어 단어 필터
    FORBIDDEN_WORDS = [
        r'\bmasih\b', r'\bdan\b', r'\bdengan\b', r'\buntuk\b',
        r'\bjuga\b', r'\batau\b', r'\btidak\b', r'\byang\b',
        r'\bini\b', r'\bitu\b', r'\bsaya\b', r'\bkamu\b',
        r'\bada\b', r'\bbisa\b', r'\bharus\b', r'\bsudah\b',
        r'\bakan\b', r'\bagar\b', r'\bpada\b', r'\bdari\b',
    ]
    for pattern in FORBIDDEN_WORDS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # 연속 공백 다시 정리
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

def clean_obj(obj):
    if isinstance(obj, str): return strip_hanja(obj)
    if isinstance(obj, dict): return {k: clean_obj(v) for k,v in obj.items()}
    if isinstance(obj, list): return [clean_obj(i) for i in obj]
    return obj

# ── 타 커리큘럼명 누수 방지 사후 필터 ──────────────────────
_GLOBAL_BANNED_CURRICULA = [
    "인셉션", "O.V.S", "OVS", "파노라마", "뉴런",
    "R'gorithm", "Starting Block", "KICE Anatomy",
    "세젤쉬", "All Of KICE", "VIC-FLIX",
    "KISS Logic", "KISSAVE", "KISSCHEMA",
]

def ban_other_curricula(result, plabel: str):
    """
    AI 출력 전체(dict/list/str)를 재귀 탐색해,
    현재 강좌명(plabel)과 무관한 커리큘럼명을 plabel로 교체한다.
    """
    if not plabel:
        return result

    plabel_lower = plabel.replace(" ", "").lower()

    # 현재 강좌명에 포함된 단어는 금지 대상에서 제외
    forbidden = [
        name for name in _GLOBAL_BANNED_CURRICULA
        if name.replace(" ", "").lower() not in plabel_lower
    ]

    # 강사 DB 시그니처 메서드도 추가
    ip = st.session_state.get("inst_profile") or {}
    for m in (ip.get("signatureMethods") or []):
        if m and m != "없음" and m.replace(" ", "").lower() not in plabel_lower:
            if m not in forbidden:
                forbidden.append(m)

    def _clean(obj):
        if isinstance(obj, str):
            for f in forbidden:
                if f in obj:
                    obj = obj.replace(f, plabel)
            return obj
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_clean(i) for i in obj]
        return obj

    return _clean(result)
    
def safe_json(raw: str) -> dict:
    import json, re
    
    start = raw.find('{')
    if start == -1:
        raise ValueError(f"JSON 시작점 찾기 실패:\n{raw[:100]}")
        
    depth = 0
    in_string = False
    escape = False
    end = -1
    
    # 스택 알고리즘으로 정확히 일치하는 마지막 '}' 를 찾아냅니다.
    for i in range(start, len(raw)):
        c = raw[i]
        if escape:
            escape = False
            continue
        if c == '\\':
            escape = True
            continue
        if c == '"':
            in_string = not in_string
            continue
            
        if not in_string:
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
                    
    if end == -1:
        raise ValueError(f"JSON이 중간에 끊겼습니다(AI 출력 제한):\n{raw[:100]}...")
        
    s = raw[start:end+1]
    s = s.replace('\n', ' ').replace('\r', ' ')
    s = re.sub(r",\s*}", "}", s)
    s = re.sub(r",\s*]", "]", s)
    
    try:
        return clean_obj(json.loads(s))
    except Exception as e:
        raise ValueError(f"JSON 파싱 에러: {e}\n추출된 문자열: {s[:100]}")
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
    # 사진을 못 찾았을 경우 엉뚱한 사진 대신 배경색을 쓰도록 빈 값 반환
    return ""


# ══════════════════════════════════════════════════════
# AI 호출
# ══════════════════════════════════════════════════════
def call_ai(prompt: str, system: str = "", max_tokens: int = 2000) -> str:
    key = st.session_state.api_key.strip()
    if not key:
        raise ValueError("API 키가 없습니다. 사이드바에서 gsk_... 키를 입력해주세요.")
    messages = []
    sys_parts = [system] if system else []
    sys_parts.append(
    "Return ONLY valid JSON. No markdown. No extra text. "
    "CRITICAL: Never use Chinese, Japanese, Indonesian, Malay words. "
    "Forbidden words: masih, dan, dengan, untuk, juga, atau, tidak, yang, ini. "
    "Write ALL body text in Korean only. English is allowed ONLY for brand slogans and course names."
    )
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
    ptype_hint = PURPOSE_THEME_HINTS.get(ptype, "")
    color_hint = ""
    for kw, hint in MOOD_COLOR_HINTS.items():
        if kw.lower() in mood.lower():
            color_hint = f"\n\n⚠️ 색상 필수 지침: {hint}"
            break
            
    lg = {"brutal":"sharp 0px radius, heavy uppercase, raw contrast",
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
          
    prompt = f"""한국 교육 랜딩페이지 디자인 생성. 당신은 Apple, Stripe의 수석 웹 디자이너입니다.

무드: "{mood}"
레이아웃: {seed.get("layout","auto")} ({lg})
폰트: {fg}
파티클: {seed.get("particle","none")}
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
- extraCSS 필드는 최대한 짧게 작성하세요 (토큰 초과 방지).
- ⚠️ 쨍하고 눈 아픈 원색(순수 빨강, 순수 파랑 등)은 절대 피하세요. 채도를 약간 낮춘 세련된 톤(Pastel, Muted, or Deep)을 사용하세요.
- ⚠️ 배경이 어두울 때는 완전한 검정(#000000)보다 딥 차콜(#0A0A0A, #111111)이나 딥 네이비(#050A15)를 쓰면 훨씬 세련되어 보입니다.
- ⚠️ 텍스트 가독성은 생명입니다. 배경이 어두우면 텍스트는 무조건 #F5F5F0 같은 부드러운 흰색을, 배경이 밝으면 #111111 같은 먹색을 쓰세요.
- c1(강조색)은 버튼과 포인트 테두리에 쓰입니다. 배경과 확연히 구분되는 감각적인 색(예: 네온 그린, 코발트 블루, 앰버 골드, 코랄 핑크 등) 하나만 선택해 시선을 집중시키세요.
- displayFont: 반드시 Google Fonts에 실제로 존재하는 폰트만. 권장: 'Black Han Sans', 'Noto Sans KR', 'Bebas Neue', 'Space Grotesk', 'Playfair Display'
- heroStyle: "typographic", "cinematic", "billboard", "editorial_bold", "split", "immersive" 중 무드에 가장 잘 맞는 것.

JSON만 반환 (한 줄, extraCSS 필드 제외):
{{"name":"2-4글자+이모지","dark":true,"heroStyle":"typographic","c1":"#hex","c2":"#hex","c3":"#hex","c4":"#hex","bg":"#hex","bg2":"#hex","bg3":"#hex","textHex":"#hex","textRgb":"r,g,b","bdAlpha":"rgba(r,g,b,.15)","displayFont":"Google Font name","bodyFont":"Noto Sans KR","fontWeights":"400;700;900","displayFontWeights":"400;700","borderRadiusPx":8,"btnBorderRadiusPx":100,"particle":"{seed.get('particle','none')}","ctaGradient":"linear-gradient(135deg,#hex,#hex)"}}"""
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
    ip     = st.session_state.get("inst_profile") or {}
    name   = st.session_state.instructor_name
    subj   = st.session_state.subject
    plabel = st.session_state.get("purpose_label", "")

    sig_methods = [m for m in (ip.get("signatureMethods") or []) if m and m != "없음"]

    # ── 브랜드명과 무관한 시그니처 메서드·슬로건 완전 차단 ──
    if plabel and sig_methods:
        plabel_clean = plabel.replace(" ", "").lower()
        method_match = any(
            m.replace(" ", "").lower() in plabel_clean or
            plabel_clean in m.replace(" ", "").lower()
            for m in sig_methods
        )
        if not method_match:
            sig_methods = []   # 메서드 차단
            ip = dict(ip)      # 슬로건도 차단 (dict 복사 후 제거)
            ip.pop("slogan", None)

    if not ip.get("found") or not name:
        ctx = f"강사명: {name} | 과목: {subj}" if name else f"과목: {subj}"
        if plabel:
            ctx += f" | 강좌명(브랜드): {plabel}"
        return ctx

    parts = [
        f"강사: {name} ({subj})",
        f"⚠️ 이번 강좌명(브랜드): [{plabel}] ← 모든 문구는 이 강좌명만 기준으로 생성. 다른 커리큘럼명 절대 언급 금지.",
    ]
    # bio에서 다른 커리큘럼명 제거 후 삽입
    raw_bio = ip.get("bio", "")
    if raw_bio and plabel:
        # bio 안의 시리즈명·강좌명 단어를 전부 plabel로 마스킹
        other_methods = [m for m in (ip.get("signatureMethods") or []) if m and m != "없음"]
        for method in other_methods:
            raw_bio = raw_bio.replace(method, plabel)
        # 자주 오염되는 고유명사 패턴 추가 제거
        import re
        raw_bio = re.sub(r'(인셉션|O\.V\.S|OVS|파노라마|뉴런|R\'gorithm|KISS|Starting Block|KICE Anatomy|세젤쉬|All Of KICE|VIC-FLIX)', plabel, raw_bio)
        parts.append(f"강사 이력(참고용): {raw_bio}")
    
    # 슬로건도 같은 방식으로 세정
    raw_slogan = ip.get("slogan", "")
    if raw_slogan and sig_methods:  # 매칭된 메서드가 있을 때만 슬로건 포함
        parts.append(f"슬로건(참고용): \"{raw_slogan}\"")
    if sig_methods:
        parts.append(f"고유 학습법: {', '.join(sig_methods)}")
    else:
        parts.append(f"이번 강좌의 핵심 방법론: [{plabel}] — 이 이름으로만 설명할 것")
    if ip.get("teachingStyle"):
        parts.append(f"강의 스타일: {ip['teachingStyle']}")
    if ip.get("desc"):
        parts.append(f"차별점: {ip['desc']}")

    return "\n".join(parts)

# ═══════════════════════════════════════════════════════
# [추가] 페이지 테마 선언문 생성 — 모든 섹션의 방향을 통일
# ═══════════════════════════════════════════════════════
def gen_theme_declaration(ctx: str, ptype: str) -> dict:
    """
    문구 생성 전에 '이 페이지의 모든 섹션이 따를 방향'을 먼저 정합니다.
    예: "6월 모평 D-30" → 모든 섹션이 '긴박감과 지금의 중요성'을 담게 됩니다.
    """
    prompt = f"""수능 교육 랜딩페이지 카피 디렉터.
    
페이지 맥락: "{ctx}"
페이지 목적: {ptype}

이 페이지의 '테마 선언문'을 만들어라.
테마 선언문 = 배너부터 CTA까지 모든 섹션이 공유할 핵심 감정/시기/메시지 방향.

규칙:
- 맥락에서 핵심 키워드를 뽑아라 (시험명, 시즌, 강사 특징 등)
- 모든 섹션이 이 방향 안에서 일관되게 작동해야 함
- 구체적인 시기/상황이 있으면 반드시 반영 (예: 6월 모평, 3월 개강, 수능 D-100)

좋은 예시:
- "6월 모평 직전이다. 이제 공부량이 아니라 '방향'이 성적을 가른다. 
  모든 섹션은 '지금 바꾸지 않으면 6월 모평에서 후회한다'는 긴박감으로 통일."
- "3월 첫 주, 수험생이 새 마음으로 시작점에 섰다. 
  모든 섹션은 '올바른 방향 설정이 1년을 좌우한다'는 희망과 전략으로 통일."
- "수능이 100일 남았다. 뉴런으로 개념-문제 괴리를 끊어낼 마지막 기회.
  모든 섹션은 '지금 뉴런이 아니면 없다'는 확신으로 통일."

나쁜 예시 (절대 이렇게 하지 말 것):
- "체계적인 학습을 통해 성적을 향상시키는 방향" (너무 일반적)
- "최고의 강사와 함께하는 커리큘럼" (AI 클리셰)

JSON만 반환:
{{"declaration": "이 페이지 전체 방향 선언문 (2-3문장, 구체적 상황 포함)", 
  "core_keyword": "이 페이지의 핵심 키워드 단어 하나 (예: 뉴런, 6월모평, KISS)",
  "emotional_tone": "감정 방향 (예: 긴박·도전, 희망·시작, 프리미엄·신뢰, 공감·따뜻)",
  "forbidden_phrases": ["이 페이지에서 쓰면 안 되는 클리셰1", "클리셰2", "클리셰3"]}}"""
    try:
        result = safe_json(call_ai(prompt, max_tokens=500))
        return result
    except Exception:
        # 실패해도 괜찮음 — 기본값 반환
        return {
            "declaration": ctx,
            "core_keyword": ctx.split()[0] if ctx else "수능",
            "emotional_tone": "도전·성장",
            "forbidden_phrases": ["체계적인", "최고의", "합리적인"]
        }
        
def gen_copy(ctx: str, ptype: str, tgt: str, plabel: str) -> dict:
    inst_ctx = _get_instructor_context()
    variation_hint = get_copy_variation()
    theme_decl = gen_theme_declaration(ctx, ptype)
    declaration = theme_decl.get("declaration", ctx)
    core_keyword = theme_decl.get("core_keyword", "")
    st.session_state["_theme_declaration"] = theme_decl

    metaphor = st.session_state.get("metaphor", "").strip()
    if metaphor:
        metaphor_prompt = (
            f"\\n\\n"
            f"★★★ [필수 반영 — 무시 시 전체 실패] 핵심 기획 메타포: [{metaphor}] ★★★\\n"
            f"아래 3개 항목에 반드시 이 메타포를 구체적으로 녹여야 합니다:\\n"
            f"  1) bannerTitle 또는 bannerLead — 메타포의 핵심 이미지를 제목/리드에 직접 사용\\n"
            f"  2) whyReasons 중 1개 이상 — 제목 또는 설명에서 메타포 용어/개념 활용\\n"
            f"  3) ctaSub — 메타포와 수강신청을 연결하는 한 문장\\n"
            f"\\n[메타포 활용 예시 — 메타포가 \'Surfing\'이라면]\\n"
            f"  bannerTitle: \'파도를 읽는 자가 1등급을 탄다\'\\n"
            f"  whyReason: \'파도처럼 밀려오는 지문 구조를 먼저 읽어내는 눈을 만든다\'\\n"
            f"  ctaSub: \'지금 파도에 올라타지 않으면, 다음 파도를 기다려야 합니다\'\\n"
            f"\\n주의: 메타포 단어를 억지로 반복하지 말고, 의미·이미지를 문장에 자연스럽게 녹일 것.\\n"
            f"메타포: [{metaphor}] — 이 단어의 뜻, 느낌, 연상 이미지를 최대한 활용하세요.\\n"
        )
    else:
        metaphor_prompt = ""

    # ✅ 강좌명 추출 (sec_id 없음 — gen_copy 전용)
    course_name = plabel.strip() if plabel else ctx.strip()[:10]

    tone_instruction = COPY_TONES.get(st.session_state.copy_tone, "")

    schemas = {
        "신규 커리큘럼": (
            '{"bannerSub":"12자 이내 — 과목+포지셔닝","bannerTitle":"반드시 강좌명 포함 20자 이내 선언형",'
            '"brandTagline":"영문 슬로건 — 강좌명의 의미를 담은 한 문장",'
            '"bannerLead":"학생의 현실 상황을 팩트로 찌르는 문장. 최소 80자. 구체적인 상황 묘사 필수",'
            '"bannerTags":["핵심키워드1","핵심키워드2","핵심키워드3"],'
            '"bannerVisual":"[Visual Directing] 배너 시각 연출 디렉션 60자 이상",'
            '"ctaCopy":"행동 유도 10자","ctaTitle":"CTA 제목 20자",'
            '"ctaSub":"수강신청 동기부여 — 최소 50자. 지금 신청해야 하는 이유 구체적으로",'
            '"ctaBadge":"15자 이내","introTitle":"강사 소개 제목 20자",'
            '"introDesc":"강사의 차별점과 철학을 담은 본문 — 최소 120자. 학생이 느끼는 변화 중심으로",'
            '"introBio":"강사 핵심 강점 한줄 요약 — 최소 60자",'
            '"introVisual":"[Visual Directing] 인트로 시각 연출 60자 이상",'
            '"whyTitle":"수강 이유 섹션 제목 20자","whySub":"서브 제목 30자 — 구체적 상황 언급",'
            '"whyReasons":[["01","임팩트 있는 짧은 제목 12자","학생 관점에서 구체적 설명 최소 100자 — 왜 이 강의여야 하는지 팩트 중심"],["02","제목 12자","100자 이상 설명"],["03","제목 12자","100자 이상 설명"]],'
            '"whyVisual":"[Visual Directing] 수강이유 섹션 시각 연출 60자 이상",'
            '"curriculumTitle":"커리큘럼 섹션 제목 20자","curriculumSub":"서브 제목 30자",'
            '"curriculumSteps":[["01","단계명 8자","이 단계를 통해 학생에게 무슨 변화가 생기는지 70자 이상 구체적 설명","기간"],["02","8자","70자 이상","기간"],["03","8자","70자 이상","기간"],["04","8자","70자 이상","기간"]],'
            '"targetTitle":"수강 대상 제목 20자",'
            '"targetItems":["이런 학생을 위한 구체적 상황 묘사 50자 이상","50자 이상","50자 이상","50자 이상"],'
            '"reviews":[["생생하고 구체적인 후기 — 등급·점수·변화 언급 필수 70자 이상","이름","뱃지"],["70자 이상","이름","뱃지"],["70자 이상","이름","뱃지"]],'
            '"videoTitle":"영상 섹션 제목 20자","videoSub":"영상 설명 40자","videoTag":"OFFICIAL TRAILER"}'
        ),
        "이벤트": (
            '{"bannerSub":"10자","bannerTitle":"반드시 강좌명 포함 이벤트 제목 15자","brandTagline":"분위기 문장",'
            '"bannerLead":"60-90자 긴박감 리드","bannerTags":["특징1","특징2","특징3"],'
            '"bannerVisual":"[Visual Directing] 50자","ctaCopy":"10자","ctaTitle":"CTA",'
            '"ctaSub":"서브문구","ctaBadge":"15자","eventTitle":"20자","eventDesc":"50자 이상",'
            '"eventDetails":[["일정","날짜"],["대상","값"],["혜택","값"]],'
            '"benefitsTitle":"20자","eventBenefits":[{"no":"01","title":"혜택명","desc":"50자","badge":"8자"},'
            '{"no":"02","title":"혜택명","desc":"50자","badge":"8자"},{"no":"03","title":"혜택명","desc":"50자","badge":"8자"}],'
            '"deadlineTitle":"20자","deadlineMsg":"70자 긴박감"}'
        ),
        "기획전": (
            '{"festHeroTitle":"반드시 강좌/기획전명 포함 15자","festHeroCopy":"30자","festHeroSub":"50자 이상",'
            '"brandTagline":"분위기 문장","festHeroVisual":"[Visual Directing] 50자",'
            '"festHeroStats":[["수치","라벨"],["수치","라벨"]],"festLineupTitle":"20자","festLineupSub":"40자",'
            '"festLineup":[{"name":"강사명","tag":"분야","tagline":"40자","badge":"뱃지"},'
            '{"name":"강사명","tag":"분야","tagline":"40자","badge":"뱃지"}],'
            '"festBenefitsTitle":"20자","festBenefits":[{"no":"01","title":"혜택명","desc":"50자","badge":"8자"},'
            '{"no":"02","title":"혜택명","desc":"50자","badge":"8자"}],'
            '"festCtaTitle":"CTA제목","festCtaSub":"50자 이상"}'
        ),
    }

    # 강사 DB에 있는 타 커리큘럼명 수집 (금지어 목록용)
    ip_profile = st.session_state.get("inst_profile") or {}
    all_methods = [m for m in (ip_profile.get("signatureMethods") or []) if m and m != "없음"]
    forbidden_names = [m for m in all_methods if m.replace(" ","").lower() not in course_name.replace(" ","").lower()]
    forbidden_str = ", ".join(f'"{m}"' for m in forbidden_names) if forbidden_names else "없음"

    prompt = f"""당신은 대한민국 최고 수능 강사 브랜딩 카피라이터입니다.

━━━ 절대 규칙 (어기면 전체 무효) ━━━
① bannerTitle = 반드시 강좌명 "{course_name}" 포함. 20자 이내. 명사형·선언형만.
   ✅ 허용: "{course_name}" / "{course_name}으로 끝낸다" / "국어의 {course_name}"
   ❌ 금지: 문장형("~하세요"), 질문형("~인가요?"), 강좌명 없는 제목
   ❌ 금지: "4등급→1등급" "3개월만에" 등 근거 없는 수치 약속
② 이모지 금지 (brandTagline 영문 제외)
③ masih, dan, dengan 등 인도네시아어 금지
④ "체계적", "최고의", "함께라면", "실력 향상" 등 AI 클리셰 금지
⑤ 확인 안 된 수치(합격생 수, 만족도%, 등급 변화 수치) 지어내기 금지
⑥ D-day 숫자 절대 금지:
   "D-100", "D-30", "D-365", "D-50" 등 구체적 숫자가 포함된
   D-day 표현은 단 하나도 쓰지 마세요.
   → 대신: "수능 전", "지금 이 순간", "남은 시간", "수능까지" 처럼
     숫자 없는 시간 표현만 허용.
   ❌ 금지 패턴 예시: D-\\d+, D-[0-9]+
   ✅ 허용 표현: "수능 전 마지막", "지금 당장", "수능까지 남은 시간"
⑦ 현재 날짜 기준으로 계산이 필요한 모든 수치는 작성 금지.
⑧ 아래 클리셰 표현 절대 금지:
   "비밀을 공개", "비법 공개", "급상승의 비밀", "성적 급상승",
   "함께라면 가능", "살길이다", "유일한 선택", "마지막 기회"
   → 대신 학생의 현재 상황을 구체적 팩트로 묘사할 것.
   
━━━ 이번 생성 방향 ━━━
{variation_hint}
핵심 키워드: [{core_keyword}]
방향성: {declaration}{metaphor_prompt}
강좌명: {course_name}
페이지 맥락: {ctx}

━━━ 강사 정보 ━━━
{inst_ctx}

━━━ 카피 어조 ━━━
{tone_instruction}

━━━ 참고 스타일 (이 수준으로 작성) ━━━
[bannerTitle 좋은 예]
- 진또배기
- 진또배기 — 국어의 본질
- 뉴런, 이제 다르게 푼다
- KISS Logic

[bannerLead 좋은 예]
- 지문은 읽히는데 답이 안 보인다면, 읽는 방법이 틀린 겁니다.
- 국어 공부는 했는데 모평에서 왜 틀리는지 모르겠다면.
- 감이 아니라 구조로 읽으면, 수능 국어가 달리 보입니다.

[whyReasons 좋은 예]
- "기출을 풀었지만 왜 틀렸는지 모른다면, 다음 시험도 같은 자리에서 틀린다. 진또배기는 답보다 원리를 먼저 가르칩니다."
- "국어 지문에는 구조가 있습니다. 이 구조를 보는 눈을 만드는 것이 진또배기의 시작입니다."

━━━ JSON만 반환 (마크다운 금지) ━━━
{schemas.get(ptype, schemas['신규 커리큘럼'])}"""

    result = safe_json(call_ai(prompt, max_tokens=3500))
    plabel = st.session_state.get("purpose_label", "").strip()
    return ban_other_curricula(result, plabel)

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

# 문구 패턴 변주 시드 — 매 호출마다 랜덤으로 하나를 선택해서 프롬프트에 삽입
COPY_VARIATION_SEEDS = [
    {
        "style": "대비형",
        "bannerTitle_hint": "수험생이 지금 하고 있는 '잘못된 공부법'을 제목에 직접 언급하고 뒤집어라",
        "lead_hint": "지금 하는 공부 방식의 문제점을 먼저 짚고 → 해결책으로 이 강의를 제시",
        "why_hint": "각 이유를 '기존 방법 문제점 → 이 강의의 해결' 대비 구조로 작성",
        "cta_hint": "지금 당장 바꾸지 않으면 생기는 손해를 한 문장으로",
    },
    {
        "style": "감성공감형",
        "bannerTitle_hint": "수험생이 새벽에 혼자 공부하다 느끼는 외로움·막막함을 제목에 담아라",
        "lead_hint": "수험생의 현재 감정 상태를 정확히 묘사한 뒤 → 선생님이 그 옆에 있겠다는 약속",
        "why_hint": "각 이유를 선배의 경험담처럼 서술 — '저도 그 느낌 알아요'로 시작",
        "cta_hint": "시작이 두려운 수험생에게 첫 발자국을 내딛게 하는 따뜻한 문장",
    },
    {
        "style": "데이터·증거형",
        "bannerTitle_hint": "구체적 학습법 키워드(R'gorithm·KISS·인셉션 등)를 전면에 내세워라",
        "lead_hint": "이 강의가 다른 강의와 다른 '방법론적 근거'를 1~2문장으로 제시",
        "why_hint": "각 이유를 기출 데이터·출제 원리 등 검증 가능한 근거로 뒷받침",
        "cta_hint": "선택의 기준을 '느낌'이 아닌 '방법론'으로 제시하는 문장",
    },
    {
        "style": "긴박감·시간압박형",
        "bannerTitle_hint": "수능까지 남은 기간의 긴박함을 제목에 직접 숫자 또는 시간으로 표현",
        "lead_hint": "지금 당장 시작하지 않으면 수능에서 손해 보는 이유를 구체적으로",
        "why_hint": "각 이유를 '지금 이 시기에 반드시 해야 하는 이유'로 작성",
        "cta_hint": "오늘 신청하는 것이 내일 신청하는 것보다 유리한 이유",
    },
    {
        "style": "브랜드·프리미엄형",
        "bannerTitle_hint": "강사의 시그니처 커리큘럼명을 제목의 절반 이상을 차지하게 크게 배치",
        "lead_hint": "이 강의를 선택한 것이 수험생 인생에서 중요한 결정임을 고급스럽게 표현",
        "why_hint": "각 이유를 강사의 철학·방법론의 독창성 관점에서 작성",
        "cta_hint": "선택받은 소수만이 이 커리큘럼을 경험한다는 프리미엄 문장",
    },
    {
        "style": "Before/After 스토리형",
        "bannerTitle_hint": "수강 전 학생의 상황(막막함·실패·좌절)이 달라지는 전환점으로서의 제목",
        "lead_hint": "구체적인 수강생의 변화 스토리를 2~3문장으로 미리 암시",
        "why_hint": "각 이유를 '수강 전에는 이랬는데 → 수강 후에는 이렇게 달라졌다'로",
        "cta_hint": "이 강의가 학생의 수험생활에서 '전환점'이 된다는 선언",
    },
    {
        "style": "도발·직설형",
        "bannerTitle_hint": "수험생이 지금 하고 있는 비효율적인 공부를 직접 저격하는 제목",
        "lead_hint": "듣기 불편하지만 사실인 이야기를 단도직입적으로. 쉼표 없이 짧은 문장들",
        "why_hint": "각 이유를 수험생의 반박을 미리 예상하고 정면 반박하는 구조로",
        "cta_hint": "더 이상 망설이는 것 자체가 손해라는 직설적 선언",
    },
    {
        "style": "숫자·구체형",
        "bannerTitle_hint": "막연한 '성적 향상' 대신 '3월→6월' '4등급→1등급' 같은 구체적 숫자를 제목에 넣어라",
        "lead_hint": "학생이 지금 몇 등급이고, 몇 주 후에 어떻게 달라지는지 수치로 약속",
        "why_hint": "각 이유를 '학생 행동' → '결과 수치' 구조로 작성 (예: 하루 30분 → 한 달 후 차이)",
        "cta_hint": "지금 신청하면 몇 일 후에 뭘 받을 수 있는지 구체적으로",
    },
    {
        "style": "질문 연속형",
        "bannerTitle_hint": "제목 전체를 학생이 스스로에게 묻는 질문으로 만들어라 ('아직도 감으로 풀고 있나요?')",
        "lead_hint": "3개의 짧은 질문을 연속으로 던진 뒤, 마지막에 이 강의가 답임을 제시",
        "why_hint": "각 이유를 학생이 자주 하는 착각/오해를 질문으로 시작해 반박하는 구조",
        "cta_hint": "마지막 질문 하나 + '이 강의가 그 답입니다'",
    },
    {
        "style": "💥 극단적 팩트폭력형",
        "bannerTitle_hint": "학생의 뼈를 때리는 가장 현실적이고 차가운 팩트를 제목으로 작성",
        "lead_hint": "희망고문 없이, 지금 성적이 안 나오는 이유를 아주 차갑고 논리적으로 분석",
        "why_hint": "감정적인 위로를 다 빼고, 오직 데이터와 팩트만으로 압도할 것",
        "cta_hint": "'할 테면 해보든가' 식의 엄청난 자신감을 보여주는 차가운 한 문장"
    },
    {
        "style": "🔮 사이비 교주형 (광기)",
        "bannerTitle_hint": "마치 홀린 듯이 이 강의를 들을 수밖에 없게 만드는 맹신적인 제목",
        "lead_hint": "다른 강사를 들으면 망할 것처럼, 오직 나만이 구원자라는 뉘앙스로 작성",
        "why_hint": "이유를 묻지도 따지지도 말고 그냥 따라오라는 식의 압도적인 확신",
        "cta_hint": "1등급을 향한 마지막 동아줄임을 강조하는 다급한 문장"
    },
]
 
def get_copy_variation() -> str:
    """매 호출마다 다른 문구 변주 지시를 반환"""
    v = _random.choice(COPY_VARIATION_SEEDS)
    return (
        f"\n\n===이번 생성의 문구 스타일 지침 [{v['style']}]===\n"
        f"- bannerTitle 방향: {v['bannerTitle_hint']}\n"
        f"- bannerLead/introDesc 방향: {v['lead_hint']}\n"
        f"- whyReasons 방향: {v['why_hint']}\n"
        f"- ctaSub/ctaTitle 방향: {v['cta_hint']}\n"
        f"※ 위 스타일을 반드시 반영해 기존 예시와 완전히 다른 문구를 생성하라."
    )
    
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
# ═══════════════════════════════════════════════════════
# 강좌 소개 AI 생성
# ═══════════════════════════════════════════════════════
def gen_course_copy(course_info: str) -> dict:
    """사용자가 입력한 강좌 정보 → AI 문구 생성"""
    plabel = st.session_state.get("purpose_label", "").strip()
    subj   = st.session_state.get("subject", "국어")
    ip     = st.session_state.get("inst_profile") or {}

    all_methods   = [m for m in (ip.get("signatureMethods") or []) if m and m != "없음"]
    plabel_lower  = plabel.replace(" ", "").lower()
    forbidden_names = [
        m for m in all_methods
        if m.replace(" ", "").lower() not in plabel_lower
    ]
    forbidden_str = ", ".join(f'"{m}"' for m in forbidden_names) if forbidden_names else "없음"

    prompt = f"""수능 교육 랜딩페이지 강좌 소개 섹션 카피라이터.

과목: {subj}
강좌명(브랜드): {plabel}

사용자가 입력한 강좌 정보:
"{course_info}"

━━━ 절대 규칙 ━━━
① 이번 강좌명: "{plabel}" — 모든 문구에서 이 이름만 사용
② 금지 단어 (다른 커리큘럼명): {forbidden_str} — 이 단어들은 단 한 글자도 쓰지 말 것
③ 입력된 정보에 없는 내용은 지어내지 말 것 (강사명을 coursePoints 제목으로 쓰는 것 금지)
④ coursePoints 제목에는 반드시 "{subj}"와 관련된 학습 내용/특징만 — 강사명·강사 소개 절대 금지
⑤ coursePoints title은 "{subj}" 포함 15자 이내 구체적 학습 항목으로 작성
⑥ 모든 텍스트는 완전한 한국어 문장 — 단어 중간에서 끊기거나 첫 글자가 빠지는 것 금지
⑦ 과목명({subj})을 줄이거나 생략하지 말 것 (예: "국어 원리"를 "어 원리"로 쓰는 것 금지)

규칙:
- courseTitle: 강좌명 또는 강좌를 가장 잘 표현하는 제목 (20자 이내)
- courseSub: 이 강좌가 필요한 이유 한 문장 (30자 이내, 반드시 완전한 문장)
- courseDesc: 강좌의 핵심 특징 설명 (60-100자, 구체적으로, 완전한 문장)
- coursePoints: 강좌 핵심 포인트 3개
  - icon: 이모지 1개
  - title: {subj}와 관련된 학습 내용 15자 이내 (강사명 금지, 반드시 완전한 단어)
  - desc: 구체적 설명 40자 이내 (완전한 문장)
- courseDuration: 강좌 기간 (입력 정보에 있으면 사용, 없으면 빈 문자열)
- courseLevel: 수준 (입력 정보에 있으면 사용, 없으면 빈 문자열)
- courseTag: 강좌 특징 키워드 3개 (과목명 포함, 완전한 단어)

JSON만 반환 (마크다운 절대 금지):
{{"courseTitle":"{plabel}","courseSub":"{subj} 강좌가 필요한 이유 30자",
"courseDesc":"강좌 핵심 특징 60-100자 설명",
"coursePoints":[
  {{"icon":"📖","title":"{subj} 핵심 포인트1","desc":"구체적 설명 40자"}},
  {{"icon":"⚡","title":"{subj} 핵심 포인트2","desc":"구체적 설명 40자"}},
  {{"icon":"🎯","title":"{subj} 핵심 포인트3","desc":"구체적 설명 40자"}}
],
"courseDuration":"","courseLevel":"","courseTag":["{subj}","진또배기","수능"]}}"""

    result = safe_json(call_ai(prompt, max_tokens=1000))

    # ── 사후 검증: 깨진 텍스트 탐지 및 보정 ──
    points = result.get("coursePoints", [])
    cleaned_points = []
    for pt in points:
        if not isinstance(pt, dict):
            continue
        title = pt.get("title", "")
        desc  = pt.get("desc", "")
        # 강사명이 포인트 제목으로 들어온 경우 제거
        inst_name = st.session_state.get("instructor_name", "")
        if inst_name and inst_name in title:
            continue
        # 너무 짧거나 의미없는 포인트 제거
        if len(title) < 2 or len(desc) < 5:
            continue
        cleaned_points.append(pt)

    if cleaned_points:
        result["coursePoints"] = cleaned_points

    # ── 타 커리큘럼명 누수 제거 ──
    return ban_other_curricula(result, plabel)


def gen_textbook_copy(textbook_info: str) -> dict:
    """사용자가 입력한 교재 정보 → AI 문구 생성"""
    plabel = st.session_state.get("purpose_label", "").strip()
    ip     = st.session_state.get("inst_profile") or {}

    all_methods   = [m for m in (ip.get("signatureMethods") or []) if m and m != "없음"]
    plabel_lower  = plabel.replace(" ", "").lower()
    forbidden_names = [
        m for m in all_methods
        if m.replace(" ", "").lower() not in plabel_lower
    ]
    forbidden_str = ", ".join(f'"{m}"' for m in forbidden_names) if forbidden_names else "없음"

    inst_ctx_raw = _get_instructor_context()

    prompt = f"""수능 교육 랜딩페이지 교재 소개·판매 섹션 카피라이터.

강사/과목 정보:
{inst_ctx_raw}

사용자가 입력한 교재 정보:
"{textbook_info}"

━━━ 절대 규칙 ━━━
① 이번 강좌명: "{plabel}" — 모든 문구에서 이 이름만 사용
② 금지 단어 (다른 커리큘럼명): {forbidden_str} — 이 단어들은 단 한 글자도 쓰지 말 것
③ 입력된 정보에만 기반하고 없는 내용은 지어내지 말 것

규칙:
- tbTitle: 교재명 또는 시리즈명 (20자 이내)
- tbSub: 이 교재가 특별한 이유 한 문장 (30자 이내)
- tbDesc: 교재 소개 (60-100자)
- tbBooks: 교재 구성 목록. [{{"name":"권명","desc":"이 권의 역할 20자","badge":"필수/추천/심화"}}]
- tbFeatures: 교재 특징 3가지 [{{"icon":"이모지","feature":"특징 20자"}}]
- tbBuyTitle: 구매 유도 제목 (20자)
- tbBuyDesc: 구매 유도 설명 (40자)

JSON만 반환:
{{"tbTitle":"교재명","tbSub":"30자","tbDesc":"60-100자",
"tbBooks":[{{"name":"권명","desc":"역할 20자","badge":"필수"}}],
"tbFeatures":[{{"icon":"이모지","feature":"특징 20자"}},{{"icon":"이모지","feature":"20자"}},{{"icon":"이모지","feature":"20자"}}],
"tbBuyTitle":"구매 제목","tbBuyDesc":"40자"}}"""

    result = safe_json(call_ai(prompt, max_tokens=1200))
    # ✅ 사후 필터: 타 커리큘럼명 누수 제거
    return ban_other_curricula(result, plabel)


# ═══════════════════════════════════════════════════════
# 섹션별 문구 재생성
# ═══════════════════════════════════════════════════════
def gen_section(sec_id: str) -> dict:
    inst_ctx = _get_instructor_context()
    ptype = st.session_state.purpose_type
    course_name = st.session_state.get("purpose_label", "").strip()  # ✅ gen_section 전용

    # 🌟 부분 재생성 시에도 메인 카피는 짧게 유지 🌟
    schemas = {
        "banner": '{"bannerSub":"10자","bannerTitle":"15자 이내의 아주 짧고 압도적인 단어/구","brandTagline":"컨셉을 담은 브랜드 한 문장","bannerLead":"60-90자 수험생이 공감하는 구체적 리드","bannerTags":["키워드1","키워드2","키워드3"],"bannerVisual":"[Visual Directing] 배너 시각 연출 디렉션","ctaCopy":"10자","statBadges":[]}',
        "intro":  '{"introTitle":"20자","introDesc":"80-120자 강사 철학과 차별점","introBio":"강사 학습법 포함 60자","introVisual":"[Visual Directing] 인트로 시각 연출 디렉션","introBadges":[]}',
        "why":    '{"whyTitle":"20자","whySub":"30자","whyReasons":[["01","직설적인 짧은 제목","학생 입장에서 구체적 설명 최소 80자"],["02","12자","80자"],["03","12자","80자"]],"whyVisual":"[Visual Directing] 수강이유 섹션 시각 연출 디렉션"}',
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
    if sec_id == "banner":
        purpose_specific_rule = (
            f'⚠️ [절대규칙] bannerTitle에 반드시 강좌명 "{course_name}"이 들어가야 합니다. '
            f'문장형·질문형 금지. 명사형·선언형만 허용. '
            f'근거 없는 수치("4등급→1등급", "3개월만에") 금지. '
            f'좋은 예: "{course_name}" / "{course_name}으로 끝낸다"'
        )
    elif sec_id == "banner" and ptype == "이벤트":
        purpose_specific_rule = (
            f'⚠️ 이벤트 배너: 강좌명 "{course_name}" 포함. 혜택/기간 키워드 포함. '
            f'질문형·문장형 금지.'
        )
    user_course_info = st.session_state.get("course_info", "")
    target_directive = f"\n[⚠️ 절대 규칙]: 강사의 기존 시그니처 커리큘럼(예: KISS Logic 등)을 무작정 섞어 쓰지 마세요. 사용자가 입력한 맥락({st.session_state.purpose_label})과 강좌정보({user_course_info})에만 100% 집중하세요. 특히 '구성 안내(package)'나 '커리큘럼' 생성 시, 추상적인 강좌명을 나열하지 말고 '본교재', '워크북', '모의고사', '학습 Q&A' 같은 구체적인 실물/서비스 위주로 작성하세요."
    purpose_specific_rule += target_directive

    sec_name = SEC_LABELS.get(sec_id, sec_id)
    schema = schemas.get(sec_id, '{"title":"제목","desc":"설명"}')

    theme_decl = st.session_state.get("_theme_declaration", {})
    declaration = theme_decl.get("declaration", "")
    core_keyword = theme_decl.get("core_keyword", "")
    
    metaphor = st.session_state.get("metaphor", "").strip()
    if metaphor:
        metaphor_hint = (
            f"\\n★★★ [필수] 핵심 메타포: [{metaphor}] ★★★\\n"
            f"이 섹션의 제목(title)·설명(desc) 중 하나 이상에 "
            f"메타포의 이미지/의미를 자연스럽게 녹이세요.\\n"
            f"Visual Directing 필드가 있으면 메타포 이미지를 시각적으로 표현하세요.\\n"
        )
    else:
        metaphor_hint = ""

    declaration_hint = f"# ★ 이 섹션도 반드시 아래 방향으로 작성하세요:\n{declaration}\n# 핵심 키워드 [{core_keyword}]가 자연스럽게 녹아있어야 합니다.{metaphor_hint}" if declaration else metaphor_hint

    # 🌟 매번 누를 때마다 파격적인 프롬프트를 생성 🌟
    variation_hint = get_copy_variation()

    prompt = f"""당신은 대한민국 최고 수준의 1타 강사 프로모션 카피라이터입니다. "{sec_name}" 섹션만 새롭게 생성하세요.
{declaration_hint}

{variation_hint}

{inst_ctx}
과목: {st.session_state.subject} | 브랜드: {st.session_state.purpose_label}
카피 어조: {COPY_TONES.get(st.session_state.copy_tone, "")}

{purpose_specific_rule}

=== 🚨 카피라이팅 품질 및 이모지 규칙 🚨 ===
1. 작위적인 비유, 번역기 돌린 듯한 문장("수험생은 ~할 수 있는가?"), 어색한 단어 조합("초고속 선택")을 절대 피하세요.
2. 대치동 1타 강사들이 실제로 쓰는 세련되고 단호한 문장(존댓말 또는 부드러운 평어체)을 사용하세요.
3. 이모지는 문맥에 완벽히 어울리는 경우에만 1개 이하로 최소화해서 사용하세요. 억지로 파격적인 이모지를 넣지 마세요.
4. 버튼(CTA) 텍스트는 행동을 직관적으로 유도하는 자연스러운 한국어(예: "수강신청 바로가기", "지금 시작하기")로 작성하세요.
5. 한자 금지, 확인되지 않은 수치 지어내기 절대 금지.

아래 JSON 형식만 반환. 마크다운 금지:
{schema}"""

    last_err = None
    plabel = st.session_state.get("purpose_label", "").strip()
    for attempt in range(3):
        try:
            result = safe_json(call_ai(prompt, max_tokens=1500))
            return ban_other_curricula(result, plabel)
        except Exception as e:
            last_err = e
            time.sleep(1)

    raise last_err or Exception("AI 모델 응답 끊김 - 다시 시도해주세요.")

# ── 강사 DB ─────────────────────────────────────────
INSTRUCTOR_DB = {
    # ━━ 영어 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "이명학": {
        "found": True, "subject": "영어", "platform": "대성마이맥",
        "bio": "대성마이맥 영어 강사. R'gorithm·Syntax·Read N' Logic 시리즈로 독해 논리 체계화.",
        "slogan": "영어, 논리로 끝낸다",
        "signatureMethods": ["R'gorithm", "Syntax", "Read N' Logic"],
        "teachingStyle": "구문 분석과 독해 논리를 체계적으로 연결하는 수업",
        "desc": "R'gorithm으로 지문 구조를 논리적으로 파악하고 어떤 지문도 흔들리지 않는 독해력을 만든다",
        "curriculum_series": ["R'gorithm 기본", "SYNTAX", "Read N' Logic"],
        "target_grade": "고3·N수",
        "strength": "독해 논리 구조화",
    },
    "션티": {
        "found": True, "subject": "영어", "platform": "대성마이맥",
        "bio": "대성마이맥 영어. KISS 시리즈(KISSAVE·KISSCHEMA·KISS Logic) 수능 영어 단순화 전문.",
        "slogan": "KISS — Keep It Simple, Suneung",
        "signatureMethods": ["KISS Logic", "KISSAVE", "KISSCHEMA"],
        "teachingStyle": "수능 영어 핵심 원리를 KISS 원칙으로 단순화·반복 훈련",
        "desc": "KISS 시리즈로 처음부터 끝까지 수능 영어 완성. 복잡한 것을 단순하게 만드는 것이 진짜 실력",
        "curriculum_series": ["KISS Logic", "KISSAVE", "KISSCHEMA"],
        "target_grade": "고3·N수",
        "strength": "핵심 단순화",
    },
    "조정식": {
        "found": True, "subject": "영어", "platform": "메가스터디",
        "bio": "메가스터디 영어 강사. 수능 영어 1등급 로드맵 설계 전문.",
        "slogan": "1등급, 설계부터 다르다",
        "signatureMethods": ["1등급 로드맵", "독해 기본기"],
        "teachingStyle": "수능 영어 구조를 단계적으로 쌓아올리는 체계적 설계",
        "desc": "기초부터 1등급까지 끊어짐 없는 커리큘럼 설계",
        "curriculum_series": ["영어 기본기", "독해 완성"],
        "target_grade": "고1·2·3",
        "strength": "체계적 로드맵",
    },
    "김기훈": {
        "found": True, "subject": "영어", "platform": "EBSi",
        "bio": "EBSi 영어 대표 강사. EBS 연계 교재 완벽 분석 특화.",
        "slogan": "EBS가 답이다",
        "signatureMethods": ["EBS 완벽 연계", "기출 분석"],
        "teachingStyle": "EBS 연계율을 최대한 활용한 실전 전략 수업",
        "desc": "EBS 교재를 완벽하게 소화해 연계 70%를 확실한 점수로 전환",
        "curriculum_series": ["EBS 완성", "수능특강 분석"],
        "target_grade": "고3",
        "strength": "EBS 연계 극대화",
    },
 
    # ━━ 수학 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "이미지": {
        "found": True, "subject": "수학", "platform": "대성마이맥",
        "bio": "대성마이맥 수학. 세젤쉬·미친개념·미친기분 시리즈.",
        "slogan": "수학, 미치도록 쉽게",
        "signatureMethods": ["세젤쉬", "미친개념", "미친기분"],
        "teachingStyle": "복잡한 개념을 직관적으로 쉽게 전달",
        "desc": "세젤쉬·미친개념으로 수학 입문자도 따라오게 만드는 강사",
        "curriculum_series": ["세젤쉬", "미친개념", "미친기분"],
        "target_grade": "고1·2·3",
        "strength": "개념 직관화",
    },
    "김범준": {
        "found": True, "subject": "수학", "platform": "대성마이맥",
        "bio": "대성마이맥 수학. Starting Block·KICE Anatomy·The Hurdling.",
        "slogan": "수능 수학의 뼈대를 세워라",
        "signatureMethods": ["KICE Anatomy", "Starting Block", "The Hurdling"],
        "teachingStyle": "수능 기출 해부로 출제 원리 파악",
        "desc": "KICE Anatomy로 수능 수학 기출 원리 완전 이해",
        "curriculum_series": ["Starting Block", "KICE Anatomy", "The Hurdling"],
        "target_grade": "고3·N수",
        "strength": "기출 원리 해부",
    },
    "현우진": {
        "found": True, "subject": "수학", "platform": "메가스터디",
        "bio": "메가스터디 수학. 뉴런 시리즈. 수학 1등급 양성 전문.",
        "slogan": "수학은 뉴런이 답이다",
        "signatureMethods": ["뉴런", "수학적 사고"],
        "teachingStyle": "수학적 사고력을 기르는 개념 중심 수업",
        "desc": "뉴런 시리즈로 수학 전 영역을 하나의 흐름으로 연결",
        "curriculum_series": ["뉴런 수1", "뉴런 수2", "뉴런 미적분"],
        "target_grade": "고3·N수",
        "strength": "수학적 사고력",
    },
    "정승제": {
        "found": True, "subject": "수학", "platform": "이투스",
        "bio": "이투스 수학. 정승제 수학의 정석 시리즈. 개념 기초 특화.",
        "slogan": "수학, 기초가 전부다",
        "signatureMethods": ["개념 완성", "수학의 정석"],
        "teachingStyle": "수학 개념의 본질을 파악하는 기초 완성 수업",
        "desc": "수학 기초가 부족한 학생도 1등급을 만들어내는 개념 완성 커리큘럼",
        "curriculum_series": ["수1 완성", "수2 완성", "확통·미적분"],
        "target_grade": "고1·2·3",
        "strength": "기초 개념 완성",
    },
 
    # ━━ 국어 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "김승리": {
        "found": True, "subject": "국어", "platform": "대성마이맥",
        "bio": "대성마이맥 국어. All Of KICE·VIC-FLIX 시리즈.",
        "slogan": "국어, 승리로 끝낸다",
        "signatureMethods": ["All Of KICE", "VIC-FLIX"],
        "teachingStyle": "수능 국어 출제 원리 파악 후 실전 능력 강화",
        "desc": "All Of KICE로 국어 원리부터 실전까지 완성",
        "curriculum_series": ["All Of KICE", "VIC-FLIX"],
        "target_grade": "고3·N수",
        "strength": "출제 원리 분석",
    },
    "유대종": {
        "found": True, "subject": "국어", "platform": "대성마이맥",
        "bio": "대성마이맥 국어. 인셉션 시리즈·파노라마·O.V.S.",
        "slogan": "국어의 인셉션을 시작하라",
        "signatureMethods": ["인셉션", "O.V.S", "파노라마"],
        "teachingStyle": "인셉션 방식으로 국어 깊이 이해",
        "desc": "인셉션 시리즈로 국어 원리 차근차근 이해",
        "curriculum_series": ["인셉션 기본", "파노라마", "O.V.S"],
        "target_grade": "고2·3·N수",
        "strength": "국어 원리 심화",
    },
    "최인호": {
        "found": True, "subject": "국어", "platform": "메가스터디",
        "bio": "메가스터디 국어. 비문학 독해 전문 강사.",
        "slogan": "비문학, 읽으면 보인다",
        "signatureMethods": ["비문학 독해법", "지문 구조 분석"],
        "teachingStyle": "비문학 지문을 구조적으로 읽는 훈련 중심 수업",
        "desc": "어떤 비문학 지문도 5분 안에 구조를 파악하는 독해 훈련",
        "curriculum_series": ["비문학 완성", "독해 기초"],
        "target_grade": "고3·N수",
        "strength": "비문학 특화",
    },
 
    # ━━ 사회탐구 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "윤성훈": {
        "found": True, "subject": "사회", "platform": "대성마이맥",
        "bio": "대성마이맥 생활과 윤리·윤리와 사상 전문 강사.",
        "slogan": "윤리, 외우지 말고 이해해라",
        "signatureMethods": ["개념 구조화", "기출 선지 분석"],
        "teachingStyle": "윤리 개념을 구조화해 선지 판단력을 기르는 수업",
        "desc": "생활과 윤리를 외우는 과목이 아닌 이해하는 과목으로 바꾸는 강의",
        "curriculum_series": ["생활과 윤리 완성"],
        "target_grade": "고3·N수",
        "strength": "윤리 개념 구조화",
    },

    # ━━ 과학탐구 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "장풍": {
        "found": True, "subject": "과학", "platform": "대성마이맥",
        "bio": "대성마이맥 물리학1 전문 강사. 역학·전자기학 특화.",
        "slogan": "물리, 원리를 알면 계산이 보인다",
        "signatureMethods": ["물리 원리 시각화", "역학 완성"],
        "teachingStyle": "물리 원리를 시각화해 어떤 문제도 풀어내는 수업",
        "desc": "물리학1의 역학과 전자기학을 원리부터 실전까지 완성",
        "curriculum_series": ["물리학1 완성"],
        "target_grade": "고3·N수",
        "strength": "물리 원리 시각화",
    },
}

def search_instructor_improved(name: str, subj: str) -> dict:
    """강사 DB 먼저 확인, 없으면 AI로 검색 (더 구체적인 질문)"""
    # 1단계: 정확 매칭
    if name in INSTRUCTOR_DB:
        return INSTRUCTOR_DB[name]
    
    # 2단계: 부분 매칭 (이름 일부 포함)
    for db_name, info in INSTRUCTOR_DB.items():
        if name in db_name or db_name in name:
            return info
    
    # 3단계: AI 검색 (더 구체적인 프롬프트)
    prompt = (
        f'한국 수능 강사 "{name}" ({subj} 전문)에 대해 확실히 아는 정보만 알려줘.\n'
        f'모르는 정보는 빈 문자열로 남겨. 지어내거나 추측하지 말 것.\n'
        f'한자 금지. "교수" 직함 금지 — "강사" 또는 "선생님"만 사용.\n'
        f'JSON만 반환:\n'
        f'{{"found":true,"bio":"플랫폼+대표시리즈 포함 1~2문장","slogan":"강사 고유 슬로건 또는 빈문자열",'
        f'"signatureMethods":["고유 학습법1","고유 학습법2"],"teachingStyle":"수업 특징 1문장",'
        f'"desc":"학생이 이 강사를 선택해야 하는 차별점 1문장",'
        f'"curriculum_series":["대표 강좌명1","대표 강좌명2"],'
        f'"strength":"핵심 강점 키워드 (예: 독해 논리화, EBS 연계 특화)"}}'
    )
    try:
        return safe_json(call_ai(prompt, max_tokens=400))
    except Exception:
        return {
            "found": True, "bio": f"{subj} 강사", "slogan": "",
            "signatureMethods": [], "teachingStyle": "", "desc": "",
            "curriculum_series": [], "strength": "",
        }
        
def validate_copy(cp: dict) -> list:
    """생성된 문구에서 너무 짧은 항목을 반환"""
    warnings = []
    checks = [
        ("bannerTitle", 5,  "배너 제목"),
        ("bannerLead",  30, "배너 리드 문구"),
        ("introDesc",   40, "강사 소개 본문"),
        ("ctaSub",      15, "CTA 서브 문구"),
    ]
    for key, min_len, label in checks:
        val = cp.get(key, "")
        if isinstance(val, str) and len(val) < min_len:
            warnings.append(f"⚠️ {label}이 너무 짧습니다 ({len(val)}자 / 최소 {min_len}자)")
    steps = cp.get("curriculumSteps", [])
    for i, step in enumerate(steps):
        if isinstance(step, (list, tuple)) and len(step) >= 3:
            if len(str(step[2])) < 25:
                warnings.append(f"⚠️ 커리큘럼 STEP {i+1} 설명이 너무 짧습니다")
    return warnings
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
    bg_l = _hex_luminance(ct.get("bg", "#111"))
    tx_l = _hex_luminance(ct.get("textHex", "#fff"))
    ratio = (max(bg_l, tx_l) + 0.05) / (min(bg_l, tx_l) + 0.05)

    # ── 텍스트 대비 보정 (WCAG AA 기준 4.5:1) ──
    if ratio < 4.5:
        if bg_l < 0.18:
            # 아주 어두운 배경 → 순백에 가까운 텍스트
            ct["textHex"] = "#F5F5F0"
            ct["textRgb"] = "245,245,240"
        elif bg_l < 0.5:
            # 중간 밝기 배경 → 흰색 텍스트
            ct["textHex"] = "#FFFFFF"
            ct["textRgb"] = "255,255,255"
        else:
            # 밝은 배경 → 거의 검정 텍스트
            ct["textHex"] = "#111111"
            ct["textRgb"] = "17,17,17"

    # ── c1(강조색) 대비 보정 ──
    c1_l = _hex_luminance(ct.get("c1", "#888"))
    if bg_l < 0.18:
        # 어두운 배경 위 c1이 너무 어두우면 밝게 보정
        if c1_l < 0.15:
            ct["c1"] = "#AAFF00"   # 형광 그린 fallback
            ct["c2"] = "#CCFF44"
    elif bg_l > 0.5:
        # 밝은 배경 위 c1이 너무 밝으면 어둡게 보정
        if c1_l > 0.4:
            ct["c1"] = "#1A1A1A"
            ct["c2"] = "#444444"

    # ── bg2, bg3 자동 생성 (bg 기준 ±명도 조정) ──
    # bg2는 bg보다 약간 밝게, bg3는 더 밝게
    if bg_l < 0.18:
        # 어두운 테마
        ct.setdefault("bg2", ct.get("bg2", "#0D0D0D"))
        ct.setdefault("bg3", ct.get("bg3", "#141414"))
    else:
        # 밝은 테마
        ct.setdefault("bg2", ct.get("bg2", "#F0F0F0"))
        ct.setdefault("bg3", ct.get("bg3", "#E8E8E8"))

    return ct

def _cta_text_color(T: dict) -> dict:
    """CTA 그라디언트 평균 밝기 → 텍스트 색상 자동 결정.
    CSS var()가 섞여 있어도 안전하게 처리."""
    cta = T.get("cta", "")
    hexes = re.findall(r'#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})', cta)

    if hexes:
        lums = [_hex_luminance("#" + h) for h in hexes]
        avg_lum = sum(lums) / len(lums)
    else:
        # CSS var()만 있어 파싱 불가 → 테마의 bg 색상 휘도로 판단
        _vars = T.get("vars", "")
        _bg_hex = "#111111"
        if "--bg:" in _vars:
            try:
                _bg_hex = _vars.split("--bg:")[1].split(";")[0].strip()
            except Exception:
                pass
        bg_lum = _hex_luminance(_bg_hex)
        # 밝은 테마면 CTA도 밝다고 가정, 어두운 테마면 어둡다고 가정
        avg_lum = 0.7 if bg_lum > 0.4 else 0.1

    if avg_lum > 0.35:  # 밝은 CTA 배경 → 검은 글씨
        return {
            "txt": "#0A0A0A",
            "txt70": "rgba(10,10,10,.8)",
            "txt35": "rgba(10,10,10,.5)",
            "badge_bg": "rgba(0,0,0,.08)",
            "badge_bd": "rgba(0,0,0,.2)",
            "btn_bg": "#0A0A0A",
            "btn_col": "#fff",
            "btn2_bg": "rgba(0,0,0,.05)",
            "btn2_col": "rgba(0,0,0,.8)",
            "btn2_bd": "rgba(0,0,0,.25)",
        }
    return {             # 어두운 CTA 배경 → 흰 글씨
        "txt": "#fff",
        "txt70": "rgba(255,255,255,.75)",
        "txt35": "rgba(255,255,255,.4)",
        "badge_bg": "rgba(255,255,255,.15)",
        "badge_bd": "rgba(255,255,255,.25)",
        "btn_bg": "#fff",
        "btn_col": "#0A0A0A",
        "btn2_bg": "rgba(255,255,255,.1)",
        "btn2_col": "rgba(255,255,255,.9)",
        "btn2_bd": "rgba(255,255,255,.35)",
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

/* ✅ 신규: 스티키 스태킹 컨테이너 */
.sticky-stack{
  display:flex;
  flex-direction:column;
  gap:0;
}
.sticky-card{
  position:sticky;
  top:80px;
  z-index:1;
  margin-bottom:16px;
  transition:transform .3s, box-shadow .3s;
}
.sticky-card:nth-child(1){top:80px; z-index:10;}
.sticky-card:nth-child(2){top:96px; z-index:9;}
.sticky-card:nth-child(3){top:112px; z-index:8;}
.sticky-card:nth-child(4){top:128px; z-index:7;}

/* -- 카드 -- */
.card{background:var(--bg);border:1px solid var(--bd);border-radius:var(--r,4px);
  padding:24px;transition:transform .25s,box-shadow .25s}
.card:hover{transform:translateY(-4px);box-shadow:0 12px 40px rgba(0,0,0,.12)}

/* -- 강조 숫자 배경 데코 -- */
.num-deco{position:absolute;font-family:var(--fh);font-size:clamp(120px,18vw,220px);
  font-weight:900;line-height:1;opacity:.035;color:var(--c1);pointer-events:none;
  user-select:none;z-index:0}

/* ✅ 신규: 타이포그래피 워터마크 */
.typo-watermark{
  position:absolute;
  font-family:var(--fh);
  font-size:clamp(80px,15vw,220px);
  font-weight:900;
  line-height:1;
  opacity:0.03;
  color:var(--c1);
  pointer-events:none;
  user-select:none;
  z-index:0;
  white-space:nowrap;
  letter-spacing:-.05em;
  top:50%;
  left:50%;
  transform:translate(-50%,-50%);
  text-transform:uppercase;
}

/* -- 형광 강조 텍스트 -- */
.highlight{background:var(--c1);color:#fff;padding:0 6px;display:inline}

/* -- 타이포그래피 히어로 전용 -- */
.hero-word-accent{
  -webkit-text-stroke:2px var(--c1);
  color:transparent;
  font-family:var(--fh);
}
/* ✅ 신규: 벤토박스 레이아웃 */
.bento-grid{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  grid-template-rows:auto;
  gap:16px;
}
.bento-wide{grid-column:span 2;}
.bento-tall{grid-row:span 2;}
.bento-full{grid-column:1/-1;}
@media(max-width:768px){
  .bento-grid{grid-template-columns:1fr!important;}
  .bento-wide,.bento-tall,.bento-full{grid-column:auto!important;grid-row:auto!important;}
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

/* ✅ 신규: 텍스트 리빌(Reveal) 애니메이션 */
.reveal-wrap{
  overflow:hidden;
  display:inline-block;
}
.reveal-text{
  display:inline-block;
  transform:translateY(110%);
  opacity:0;
  transition:transform 1s cubic-bezier(.16,1,.3,1), opacity .6s ease;
}
.reveal-text.on{
  transform:translateY(0);
  opacity:1;
}
.reveal-text.d1{transition-delay:.1s}
.reveal-text.d2{transition-delay:.25s}
.reveal-text.d3{transition-delay:.4s}
.reveal-text.d4{transition-delay:.55s}

/* -- 텍스트 마키(Marquee) 애니메이션 -- */
.marquee-container {
  width: 100vw;
  max-width: 100%;
  overflow-x: hidden;
  position: absolute;
  top: 50%;
  transform: translateY(-50%) rotate(-3deg);
  white-space: nowrap;
  z-index: 0;
  pointer-events: none;
}
.marquee-content {
  display: inline-block;
  font-family: 'Black Han Sans', var(--fh);
  font-size: clamp(80px, 12vw, 200px);
  font-weight: 900;
  color: var(--c1);
  opacity: 0.05;
  line-height: 1;
  text-transform: uppercase;
  animation: marquee 20s linear infinite;
}
@keyframes marquee {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
/* 사이드바 가독성 및 UI 개선 (이미지 0, 2, 3 해결) */
/* 1. 입력 필드 텍스트 색상 해결 */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] div[data-baseweb="select"] > div > div,
[data-testid="stSidebar"] div[data-baseweb="input"] input,
[data-testid="stSidebar"] div[data-baseweb="textarea"] textarea,
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown p {
    color: white !important;
}
/* 입력 필드 플레이스홀더(안내 문구) 색상 */
[data-testid="stSidebar"] div[data-baseweb="select"] > div > div > div,
[data-testid="stSidebar"] div[data-baseweb="input"] input::placeholder {
  color: rgba(255,255,255,0.6) !important;
}

/* 2. 멀티셀렉트(섹션 ON/OFF) 태그 UI 세련되게 고치기 */
[data-testid="stSidebar"] div[data-baseweb="select"] > div > div > span[data-baseweb="tag"] {
  background-color: #161E38 !important;
  color: #C0CDE8 !important;
  border: 1px solid #343C58 !important;
  border-radius: 4px !important;
  padding: 4px 8px !important;
  font-size: 11px !important;
}
[data-testid="stSidebar"] div[data-baseweb="select"] > div > div > span[data-baseweb="tag"] svg {
  fill: #8A9AB8 !important;
}
[data-testid="stSidebar"] div[data-baseweb="select"] > div > div > span[data-baseweb="tag"]:hover {
  background-color: #232A40 !important;
}
[data-testid="stSidebar"] div[data-baseweb="select"] > div {
  background-color: #090D1C !important;
  border-color: #1A2038 !important;
}
/* ✅ 카드 본문 텍스트 강제 가독성 확보 */
.card p, .card span, .card div {
    color: var(--text) !important;
}
.card p {
    opacity: 0.75;
}
/* 수강 이유 카드 설명 텍스트 */
.sec p[style*="color:var(--t70)"] {
    opacity: 1 !important;
}
/* why/intro 섹션 카드 설명 최소 명도 보장 */
section#why .card p,
section#intro .card p {
    color: var(--text) !important;
    opacity: 0.7;
    font-weight: 500;
}
/* ================================================
   텍스트 가독성 — 핵심 3원칙
   1) 어두운 배경(bg luminance < 40%) → 텍스트 무조건 밝게
   2) 밝은 배경(bg luminance > 60%) → 텍스트 무조건 어둡게
   3) c1(강조색) 배경 위 → 무조건 흰 글씨
   ================================================ */

/* 기본 body */
body { color: var(--text); background: var(--bg); }

/* 섹션 기본 — var(--text) 사용 */
section, .sec { color: var(--text); }

/* c1 배경 위 → 흰 글씨 강제 */
[style*="background:var(--c1)"],
[style*="background: var(--c1)"] {
    color: #ffffff !important;
}
[style*="background:var(--c1)"] *,
[style*="background: var(--c1)"] * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

/* 그라디언트 배경 — Python _cta_text_color가 inline으로 처리하므로 CSS 강제 제거 */
/* CTA 섹션은 sec_cta() 함수 내 ct["txt"] 인라인 컬러로 직접 제어됨 */

/* 카드 — 배경이 bg 계열이므로 var(--text) 사용 */
.card { color: var(--text) !important; }
.card p, .card span:not([style*="background"]) {
    color: var(--text) !important;
    opacity: 0.75;
}
.card h3, .card h4,
.card > div[style*="font-weight:7"],
.card > div[style*="font-weight:8"],
.card > div[style*="font-weight:9"] {
    color: var(--text) !important;
    opacity: 1 !important;
}

/* tag-line(강조선+텍스트) — c1 색상 유지 */
.tag-line { color: var(--c1) !important; }

/* 어두운 배경(bg3, bg2) 위의 텍스트 보정 */
[style*="background:var(--bg3)"] *,
[style*="background: var(--bg3)"] *,
[style*="background:var(--bg2)"] *,
[style*="background: var(--bg2)"] * {
    color: var(--text) !important;
}

/* 완전 검정(#111, #0a0a0a 등) 배경 → 흰 글씨 강제 */
[style*="background:#111"] *,
[style*="background:#0a0a0a"] *,
[style*="background:#050505"] *,
[style*="background:#020008"] *,
[style*="background:#030703"] * {
    color: #F5F5F0 !important;
}

/* 흰색/아이보리 배경 → 검정 글씨 강제 */
[style*="background:#fff"] *,
[style*="background:#ffffff"] *,
[style*="background:#F5F5F0"] *,
[style*="background:#fafafa"] *,
[style*="background:#f5f5f5"] * {
    color: #111111 !important;
}

/* ── 교재 섹션 다크 배경 보정 (흰 글씨 강제) ── */
#textbook-sale[style*="background:#050505"] *,
section[style*="background:#050505"] * {
    color: #F5F5F0 !important;
}
section[style*="background:#050505"] h2,
section[style*="background:#050505"] h3,
section[style*="background:#050505"] .tag-line {
    color: #FFFFFF !important;
    opacity: 1 !important;
}
/* #111 카드 내 텍스트 흰 글씨 강제 */
[style*="background:#111;"] *,
[style*="background:#111 "] *,
div[style*="background:#111"][style*="border"] * {
    color: #F5F5F0 !important;
}
div[style*="background:#111"][style*="border"] h4 {
    color: #FFFFFF !important;
}
div[style*="background:#111"][style*="border"] p {
    color: #AAAAAA !important;
}

/* ── 라이트 모드 오버라이드 ── */
body.light-mode section:not([style*="background:var(--c1)"]):not([style*="linear-gradient"]) {
    background: #F5F5F0;
    color: #111111;
}
body.light-mode .card { background: #ffffff !important; }
body.light-mode .card * { color: #111111 !important; }
body.light-mode h1, body.light-mode h2, body.light-mode h3 { color: #0A0A0A !important; }
body.light-mode p { color: rgba(10,10,10,0.72) !important; }
body.light-mode [style*="background:var(--c1)"] * { color: #ffffff !important; }
body.light-mode [style*="background:linear-gradient"] *:not(.btn-s) { color: #ffffff !important; }

/* ================================================
   before/after 섹션 텍스트 강제
   ================================================ */
section#before-after [style*="background:#111"] * {
    color: #ffffff !important;
    opacity: 0.85;
}
section#before-after [style*="background:#111"] h3,
section#before-after [style*="background:#111"] div[style*="font-weight"] {
    opacity: 1 !important;
}
section#before-after [style*="background:var(--bg3)"] *,
section#before-after [style*="background:var(--c1)"] p {
    color: var(--text) !important;
}

/* ================================================
   grade_stats 수능당일 카드 — 흰 글씨 보장
   ================================================ */
section#grade-stats [style*="background:var(--c1)"] div,
section#grade-stats [style*="background:var(--c1)"] p {
    color: #ffffff !important;
    opacity: 1 !important;
}
section#grade-stats [style*="background:var(--bg3)"] div,
section#grade-stats [style*="background:var(--bg3)"] p {
    color: var(--text) !important;
    opacity: 0.82 !important;
}

/* ================================================
   BEFORE/AFTER 라벨 텍스트 강제
   ================================================ */
.ba-label-before { color: rgba(255,255,255,0.8) !important; }
.ba-label-after  { color: var(--c1) !important; }
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
            "overlay":'<div style="position:absolute;inset:0;background:rgba(0,0,0,0.60);z-index:1;pointer-events:none"></div>',
            "tc":"color:#fff","t70c":"color:rgba(255,255,255,.82)","c1c":"#fff",
            "bdc":"rgba(255,255,255,.28)","card_bg":"rgba(0,0,0,.7)",
            "btn_s":"color:#fff;border-color:rgba(255,255,255,.4)",
            "top_brd":"rgba(255,255,255,.22)","blur":"backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);"}


def sec_banner(d, cp, T):
    sub   = strip_hanja(cp.get("bannerSub", d["subject"]+" 완성"))
    title = strip_hanja(cp.get("bannerTitle", d["purpose_label"]))
    _tgt  = d.get("target", "")
    lead  = strip_hanja(cp.get("bannerLead", f"{_tgt}을 위한 커리큘럼"))
    cta   = strip_hanja(cp.get("ctaCopy", "수강신청하기"))
    bg_url = cp.get("bg_photo_url", "")
    dark   = T["dark"]
    has_bg = bool(bg_url)
 
    # ✅ FIX ①: T["dark"] 대신 실제 bg 색상 휘도로 판단
    # CSS vars에서 --bg 색상 추출 → luminance 계산
    _vars = T.get("vars", "")
    _bg_hex = "#111111"
    if "--bg:" in _vars:
        try:
            _bg_hex = _vars.split("--bg:")[1].split(";")[0].strip()
        except Exception:
            pass
    _bg_lum = _hex_luminance(_bg_hex)
    # 배경이미지 있으면 무조건 어두운 오버레이 → 흰 글씨
    # 배경이 실제로 어두우면(휘도 < 0.35) 흰 글씨
    # 배경이 밝으면(휘도 >= 0.35) 검은 글씨
    is_dark_context = has_bg or (_bg_lum < 0.35)
 
    text_col      = "#FFFFFF" if is_dark_context else "#0A0A0A"
    lead_col      = "rgba(255,255,255,0.88)" if is_dark_context else "rgba(10,10,10,0.72)"
    sub_text_col  = "#FFFFFF"   # var(--c1) 위에서 항상 흰색
    sub_bg        = "var(--c1)"
 
    shadow = "text-shadow:0 2px 20px rgba(0,0,0,0.85),0 1px 6px rgba(0,0,0,1);" if has_bg else ""
    # 밝은 배경 + 배경이미지 없을 때 → shadow 불필요
    if not is_dark_context:
        shadow = ""

    # 배경 설정
    if has_bg:
        bg_style = f"background:url('{bg_url}') center/cover no-repeat;"
        # ✅ 그라디언트 오버레이: 위는 반투명, 아래로 갈수록 더 어둡게
        overlay = (
            '<div style="position:absolute;inset:0;'
            'background:linear-gradient(to bottom,'
            'rgba(0,0,0,0.45) 0%,'
            'rgba(0,0,0,0.65) 50%,'
            'rgba(0,0,0,0.80) 100%);'
            'z-index:1;pointer-events:none"></div>'
        )
    else:
        bg_style = "background:var(--bg);" if not dark else \
                   "background:linear-gradient(180deg,var(--bg) 0%,var(--bg2) 100%);"
        overlay = ""

    # 레이아웃 변형 (해시 기반 고정)
    text_hash = sum(ord(c) for c in title + lead)
    v = (text_hash % 3) + 1

    # ──────────────────────────────────────────────
    # 공통 뱃지 HTML (bannerSub 표시용)
    # ──────────────────────────────────────────────
    sub_badge = (
        f'<div style="display:inline-block;font-size:12px;font-weight:800;'
        f'letter-spacing:0.15em;color:{sub_text_col};background:{sub_bg};'
        f'padding:7px 20px;border-radius:50px;margin-bottom:28px;'
        f'box-shadow:0 2px 12px rgba(0,0,0,0.3);">{sub}</div>'
    )

    # ──────────────────────────────────────────────
    # v1: 거대 마키 스타일 (Brutal)
    # ──────────────────────────────────────────────
    if v == 1:
        bg_text = f"{title} " * 6
        return (
            f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;'
            f'{bg_style}display:flex;flex-direction:column;justify-content:center;text-align:center;">'
            + overlay +
            f'<div class="marquee-container" style="z-index:1;">'
            f'<div class="marquee-content" style="color:var(--c1);opacity:0.07;">'
            f'{bg_text}{bg_text}</div></div>'
            f'<div style="position:relative;z-index:2;padding:0 clamp(20px,5vw,80px);'
            f'max-width:1100px;margin:0 auto;">'
            # 뱃지
            + sub_badge +
            # 메인 타이틀
            f'<h1 style="font-family:\'Black Han Sans\',var(--fh);'
            f'font-size:clamp(52px,9vw,140px);font-weight:900;line-height:1.0;'
            f'letter-spacing:-0.04em;color:{text_col};margin-bottom:32px;'
            f'word-break:keep-all;{shadow}">{title}</h1>'
            # 리드 문구
            f'<p style="font-size:clamp(15px,2vw,20px);line-height:1.85;'
            f'color:{lead_col};max-width:750px;margin:0 auto 48px;'
            f'font-weight:600;word-break:keep-all;{shadow}">{lead}</p>'
            # CTA 버튼
            f'<a href="#cta" style="display:inline-block;background:var(--c1);'
            f'color:#fff;padding:18px 52px;font-size:17px;font-weight:900;'
            f'font-family:var(--fh);text-decoration:none;'
            f'box-shadow:8px 8px 0px rgba(0,0,0,0.35);'
            f'transition:transform 0.2s;">{cta} →</a>'
            f'</div></section>'
        )

    # ──────────────────────────────────────────────
    # v2: 프리미엄 중앙 정렬 (Apple 스타일)
    # ──────────────────────────────────────────────
    elif v == 2:
        return (
            f'<section id="hero" style="position:relative;min-height:90vh;display:flex;'
            f'align-items:center;justify-content:center;text-align:center;overflow:hidden;{bg_style}">'
            + overlay +
            f'<div style="position:relative;z-index:2;max-width:980px;'
            f'padding:clamp(60px,8vw,100px) clamp(20px,5vw,60px);'
            f'display:flex;flex-direction:column;align-items:center;">'
            # 뱃지
            + sub_badge +
            # 메인 타이틀
            f'<h1 style="font-family:var(--fh);'
            f'font-size:clamp(40px,7.5vw,108px);font-weight:900;'
            f'color:{text_col};line-height:1.08;letter-spacing:-0.04em;'
            f'margin-bottom:26px;word-break:keep-all;{shadow}">{title}</h1>'
            # 리드 문구
            f'<p style="font-size:clamp(15px,1.8vw,21px);color:{lead_col};'
            f'font-weight:500;line-height:1.7;max-width:580px;'
            f'margin:0 auto 44px;word-break:keep-all;{shadow}">{lead}</p>'
            # CTA 버튼
            f'<a href="#cta" style="display:inline-flex;align-items:center;'
            f'justify-content:center;background:var(--c1);color:#fff;'
            f'padding:17px 50px;border-radius:8px;'
            f'font-size:clamp(15px,1.6vw,18px);font-weight:800;'
            f'text-decoration:none;box-shadow:0 8px 30px rgba(0,0,0,0.3);'
            f'transition:transform 0.2s;">{cta} →</a>'
            f'</div></section>'
        )

    # ──────────────────────────────────────────────
    # v3: 좌측 정렬 매거진 스타일 (Split)
    # ──────────────────────────────────────────────
    else:
        return (
            f'<section id="hero" style="position:relative;min-height:90vh;display:flex;'
            f'align-items:center;overflow:hidden;{bg_style}">'
            + overlay +
            f'<div style="position:relative;z-index:2;'
            f'padding:clamp(80px,10vw,120px) clamp(28px,6vw,80px);'
            f'width:100%;max-width:1300px;margin:0 auto;">'
            # 뱃지 (좌측 정렬)
            f'<div style="margin-bottom:24px;">{sub_badge}</div>'
            # 메인 타이틀
            f'<h1 style="font-family:var(--fh);'
            f'font-size:clamp(44px,7vw,108px);font-weight:900;'
            f'color:{text_col};line-height:1.08;letter-spacing:-0.03em;'
            f'margin-bottom:28px;word-break:keep-all;text-align:left;{shadow}">{title}</h1>'
            # 구분선
            f'<div style="width:56px;height:4px;background:var(--c1);margin-bottom:28px;"></div>'
            # 리드 문구
            f'<p style="font-size:clamp(14px,1.7vw,20px);color:{lead_col};'
            f'font-weight:500;line-height:1.85;max-width:580px;'
            f'margin-bottom:44px;text-align:left;word-break:keep-all;{shadow}">{lead}</p>'
            # CTA 버튼
            f'<div style="text-align:left;">'
            f'<a href="#cta" style="display:inline-flex;align-items:center;gap:8px;'
            f'background:var(--c1);color:#fff;'
            f'padding:16px 44px;font-size:16px;font-weight:900;'
            f'text-decoration:none;box-shadow:0 6px 24px rgba(0,0,0,0.3);'
            f'transition:transform 0.2s;">{cta} →</a>'
            f'</div></div></section>'
        )
        
def sec_intro(d, cp, T):
    label   = st.session_state.get("purpose_label", d["purpose_label"])
    subj    = d["subject"]
    tagline = strip_hanja(cp.get("brandTagline", ""))
    desc    = strip_hanja(cp.get("introDesc", f"{label}이 특별한 이유가 있습니다."))

    # ── 인셉션 등 타 커리큘럼명 desc에서 제거 ──
    _plabel = st.session_state.get("purpose_label", "")
    _BANNED = ["인셉션", "O.V.S", "OVS", "파노라마", "뉴런", "R'gorithm",
               "Starting Block", "KICE Anatomy", "세젤쉬", "All Of KICE", "VIC-FLIX",
               "KISS Logic", "KISSAVE", "KISSCHEMA"]  # ← 이 세 개 추가
    for _b in _BANNED:
        if _b.lower() not in _plabel.lower():
            desc = desc.replace(_b, _plabel if _plabel else d["subject"])

    reasons = cp.get("whyReasons", [])
    points  = []
    for r in reasons[:3]:
        if isinstance(r, (list, tuple)) and len(r) >= 3:
            points.append((str(r[0]), str(r[1]), str(r[2])))
    if not points:
        points = [("🎯", "핵심만 담았다", f"{label} 한 강좌로 {subj} 완성"),("⚡", "즉시 적용된다", "배운 내용을 바로 실전에 적용"),("📈", "결과가 달라진다", "수강 후 성적 변화 체감")]

    point_html = "".join(
        f'<div class="rv d{i+1}" style="flex:1;min-width:180px;padding:28px 24px;background:var(--bg3);border-radius:var(--r,4px);border:1px solid var(--bd);border-top:3px solid var(--c1)">'
        f'<div style="font-size:34px;margin-bottom:14px">{ic}</div>'
        f'<div style="font-family:var(--fh);font-size:15px;font-weight:800;color:var(--text);margin-bottom:8px">{strip_hanja(tt)}</div>'
        f'<p style="font-size:13px;line-height:1.8;color:var(--text);opacity:0.72;margin:0">{strip_hanja(dc)}</p>'
        f'</div>'
        for i, (ic, tt, dc) in enumerate(points)
    )

    # 무의미한 태그라인 필터링
    _BAD_TAGLINES = {
        "english", "korean", "math", "science", "tagline", "slogan",
        "없음", "없음.", "none", "n/a", "tbd", "미정",
    }
    _tagline_clean = tagline.strip().strip('"').strip("'")
    _tagline_lower = _tagline_clean.lower().replace(" ", "")
    _is_bad = (
        not _tagline_clean
        or _tagline_lower in _BAD_TAGLINES
        or len(_tagline_clean) < 6
        or _tagline_clean.lower() == "english"
        or _tagline_clean.lower() == d["subject"].lower()
    )
    tagline_html = (
        f'<div style="padding:22px 28px;background:var(--c1);border-radius:var(--r,4px);margin-bottom:20px">'
        f'<p style="font-size:clamp(15px,1.6vw,18px);font-style:italic;font-weight:700;'
        f'color:#fff;line-height:1.6;margin:0">"{_tagline_clean}"</p></div>'
    ) if not _is_bad else ""

    return (
        f'<section class="sec" id="intro"><div style="max-width:1100px;margin:0 auto">'
        f'<div class="rv" style="display:grid;grid-template-columns:1fr 1.8fr;gap:60px;align-items:center;padding-bottom:40px;border-bottom:2px solid var(--bd);margin-bottom:40px">'
        f'<div><div class="tag-line">{subj} 강좌 소개</div>'
        f'<h2 style="font-family:var(--fh);font-size:clamp(28px,4vw,52px);font-weight:900;line-height:1.05;color:var(--text);margin-bottom:14px">{label}</h2>'
        f'<div style="display:flex;align-items:center;gap:8px;margin-top:16px"><span style="font-size:10px;font-weight:800;background:var(--c1);color:#fff;padding:4px 14px;border-radius:var(--r-btn,100px)">{subj}</span><span style="font-size:10px;font-weight:700;color:var(--t45)">{d["target"]}</span></div></div>'
        f'<div>{tagline_html}<p style="font-size:15px;line-height:2;color:var(--t70)">{desc}</p></div></div>'
        f'<div style="display:flex;gap:16px;flex-wrap:wrap">{point_html}</div>'
        f'</div></section>'
    )

def sec_why(d, cp, T):
    t = strip_hanja(cp.get('whyTitle', '이 강의가 필요한 이유'))
    s = strip_hanja(cp.get('whySub', f"{d['subject']} 1등급의 비결"))
    reasons = cp.get('whyReasons', [])
    
    safe_r = []
    for it in reasons:
        if isinstance(it, (list, tuple)) and len(it) >= 3:
            safe_r.append((str(it[0]), str(it[1]), str(it[2])))
        elif isinstance(it, dict):
            safe_r.append((it.get('no','01'), it.get('title',''), it.get('desc','')))

    # 🌟 글자가 바뀔 때마다 레이아웃이 3가지 중 하나로 랜덤하게 변함 🌟
    text_hash = sum(ord(c) for c in t + s)
    v = (text_hash % 3) + 1

    if v == 1: # [스타일 1: 거대 배경 숫자 + 다크 매거진 스타일]
        bg_text = f"{t} " * 10
        rh = ""
        for i, (no, tt, dc) in enumerate(safe_r):
            align_self = "flex-start" if i % 2 == 0 else "flex-end"
            margin_top = "margin-top: -30px;" if i > 0 else "" 
            rh += (
                f'<div class="rv d{min(i+1,4)}" style="align-self:{align_self}; {margin_top} width: clamp(300px, 85%, 750px); position:relative; z-index:{i+2};">'
                # 뒤에 깔리는 거대한 투명 숫자
                f'<div style="position:absolute; top:-70px; left:-30px; font-family:var(--fh); font-size: clamp(150px, 18vw, 250px); font-weight:900; color:var(--c1); opacity:0.08; line-height:1; pointer-events:none; z-index:-1;">{i+1:02d}</div>'
                # 카드 본체 (이모지 대신 심플한 라인 디자인)
                f'<div style="background:var(--bg3); padding:50px 60px; border-radius:0; border-top: 4px solid var(--c1); box-shadow: 20px 20px 0px rgba(0,0,0,0.2);">'
                f'<div style="font-family:var(--fh); font-size: 16px; color:var(--c1); letter-spacing:0.2em; font-weight:800; margin-bottom:16px;">POINT {i+1:02d}</div>'
                f'<div style="font-family:var(--fh); font-size: clamp(28px, 3.5vw, 42px); font-weight:900; color:var(--text); margin-bottom:24px; word-break:keep-all; line-height:1.2;">{strip_hanja(tt)}</div>'
                f'<p style="font-size: clamp(16px, 1.8vw, 20px); line-height:1.9; color:var(--t70); margin:0; font-weight:500;">{strip_hanja(dc)}</p>'
                f'</div></div>'
            )
        # 핵심 영문 키워드 추출 (워터마크용)
        wm_text = t[:10].upper().replace(' ','') if t else 'WHY'
        return (
            f'<section class="sec" id="why" style="position:relative; overflow:hidden; padding: 180px 20px;">'
            f'<div class="typo-watermark">{wm_text}</div>'
            f'<div class="marquee-container"><div class="marquee-content">{bg_text}{bg_text}</div></div>'
            f'<div style="max-width:1100px; margin:0 auto; position:relative; z-index:2;">'
            f'<div class="rv" style="margin-bottom:120px; text-align:center;">'
            f'<div class="tag-line" style="justify-content:center; font-size:14px; letter-spacing:0.3em;">WHY CHOOSE US</div>'
            f'<h2 style="font-family:\'Black Han Sans\',var(--fh); font-size:clamp(40px, 6vw, 80px); font-weight:900; color:var(--text); letter-spacing:-0.05em; margin-top:20px;">{t}</h2>'
            f'<p class="sec-sub" style="margin: 24px auto 0; font-size:20px; color:var(--c1); font-weight:700;">{s}</p></div>'
            f'<div style="display:flex; flex-direction:column; gap:60px;">{rh}</div>'
            f'</div></section>'
        )

    elif v == 2: # [스타일 2: 애플 스타일 세로 정렬 (Clean & Minimal)]
        rh = ""
        for i, (no, tt, dc) in enumerate(safe_r):
            rh += (
                f'<div class="rv d{min(i+1,4)}" style="display:flex; gap:40px; align-items:flex-start; padding:50px 0; border-bottom:1px solid var(--bd);">'
                f'<div style="font-family:var(--fh); font-size:60px; font-weight:900; color:var(--c1); line-height:1; flex-shrink:0;">{i+1:02d}.</div>'
                f'<div><h3 style="font-family:var(--fh); font-size:clamp(26px, 3.5vw, 40px); font-weight:900; color:var(--text); margin-bottom:20px; letter-spacing:-0.03em;">{strip_hanja(tt)}</h3>'
                f'<p style="font-size:clamp(16px, 1.8vw, 20px); color:var(--t70); line-height:1.85; margin:0; font-weight:500;">{strip_hanja(dc)}</p></div>'
                f'</div>'
            )
        return (
            f'<section class="sec alt" id="why" style="padding: 160px 20px;">'
            f'<div style="max-width:900px; margin:0 auto;">'
            f'<div class="rv" style="text-align:left; margin-bottom:80px;">'
            f'<div class="tag-line" style="font-size:13px;">{s}</div>'
            f'<h2 style="font-family:var(--fh); font-size:clamp(45px, 6vw, 75px); font-weight:900; color:var(--text); letter-spacing:-0.04em; margin-top:16px;">{t}</h2>'
            f'</div><div style="border-top:2px solid var(--c1);">{rh}</div></div></section>'
        )

    else: # [스타일 3: 벤토박스 비대칭 그리드]
        rh = ""
        BENTO_PATTERNS = ["bento-wide", "", "bento-tall", ""]
        for i, (no, tt, dc) in enumerate(safe_r):
            bento_cls = BENTO_PATTERNS[i % len(BENTO_PATTERNS)]
            accent_h = "6px" if i == 0 else "3px"
            rh += (
                f'<div class="rv d{min(i+1,4)} {bento_cls}" '
                f'style="padding:{"48px 40px" if i==0 else "32px 28px"}; '
                f'background:{"var(--bg2)" if i%2==0 else "var(--bg3)"}; '
                f'border:1px solid var(--bd); position:relative; overflow:hidden;">'
                f'<div style="position:absolute;top:0;left:0;right:0;height:{accent_h};background:var(--c1)"></div>'
                f'<div style="font-family:var(--fh); font-size:{"20px" if i==0 else "14px"}; '
                f'font-weight:800; color:var(--c1); margin:8px 0 16px; letter-spacing:0.1em;">REASON 0{i+1}</div>'
                f'<h3 style="font-family:var(--fh); '
                f'font-size:clamp({"24px,3vw,36px" if i==0 else "18px,2.2vw,24px"}); '
                f'font-weight:900; color:var(--text); margin-bottom:20px; line-height:1.3;">'
                f'{strip_hanja(tt)}</h3>'
                f'<p style="font-size:{"16px" if i==0 else "14px"}; color:var(--t70); line-height:1.85; margin:0;">'
                f'{strip_hanja(dc)}</p>'
                f'</div>'
            )
        return (
            f'<section class="sec" id="why" style="padding:160px 20px; background:var(--bg2);">'
            f'<div style="max-width:1200px; margin:0 auto;">'
            f'<div class="rv" style="text-align:center; margin-bottom:80px;">'
            f'<div class="tag-line" style="justify-content:center;">WHY THIS CLASS</div>'
            f'<h2 style="font-family:var(--fh); font-size:clamp(36px,5vw,64px); '
            f'font-weight:900; color:var(--text);">{t}</h2>'
            f'<p style="font-size:18px; color:var(--t70); margin-top:20px;">{s}</p>'
            f'</div>'
            f'<div class="bento-grid">{rh}</div>'
            f'</div></section>'
        )
def sec_curriculum(d, cp, T):
    """커리큘럼 — 3가지 다이내믹 레이아웃"""
    t = strip_hanja(cp.get("curriculumTitle", f"{d['purpose_label']} 커리큘럼"))
    s = strip_hanja(cp.get("curriculumSub", "단계별 완성 로드맵"))
    steps = cp.get("curriculumSteps", [])
    if not steps:
        steps = [["01","개념 완성","핵심 개념을 정확히 이해","4주"], ["02","훈련","기출 완전 분석","4주"], ["03","심화","고난도 특훈","3주"], ["04","파이널","실전 완성","3주"]]

    v = (sum(ord(c) for c in t + s) % 3) + 1
    sh = ""

    if v == 1:
        # [스타일 1: 중앙 집중형 거대 넘버링 카드 (Editorial Stack)]
        for i, step in enumerate(steps):
            du = str(step[3]) if len(step) > 3 else "4주"
            sh += (
                f'<div class="rv d{min(i+1,4)} sticky-card" style="display:flex; flex-direction:column; align-items:center; text-align:center; background:var(--bg); border:1px solid var(--bd); border-radius:var(--r, 12px); padding:48px 32px; box-shadow:0 10px 30px rgba(0,0,0,0.05); margin-bottom:24px; position:relative; overflow:hidden;">'
                f'<div style="position:absolute; top:-30px; left:50%; transform:translateX(-50%); font-family:var(--fh); font-size:200px; font-weight:900; color:var(--c1); opacity:0.04; line-height:1; pointer-events:none;">{i+1:02d}</div>'
                f'<div style="display:inline-block; font-size:12px; font-weight:800; background:var(--bg3); color:var(--c1); padding:6px 16px; border-radius:100px; margin-bottom:20px; border:1px solid var(--bd); position:relative; z-index:1;">{du} 완성</div>'
                f'<h3 style="font-family:var(--fh); font-size:clamp(24px, 3.5vw, 36px); font-weight:900; color:var(--text); margin-bottom:16px; position:relative; z-index:1;">{strip_hanja(str(step[1]))}</h3>'
                f'<p style="font-size:15px; line-height:1.8; color:var(--t70); max-width:600px; margin:0; position:relative; z-index:1;">{strip_hanja(str(step[2]))}</p>'
                f'</div>'
            )
        return (
            f'<section class="sec alt" id="curriculum">'
            f'<div style="max-width:800px; margin:0 auto">'
            f'<div class="rv" style="text-align:center; margin-bottom:56px;">'
            f'<div class="tag-line" style="justify-content:center;">CURRICULUM</div>'
            f'<h2 style="font-family:var(--fh); font-size:clamp(36px, 5vw, 64px); font-weight:900; color:var(--text); letter-spacing:-0.03em; margin-bottom:16px;">{t}</h2>'
            f'<p style="font-size:16px; color:var(--t70);">{s}</p>'
            f'</div>'
            f'<div class="sticky-stack">{sh}</div>'
            f'</div></section>'
        )

    elif v == 2:
        # [스타일 2: 좌우 지그재그 타임라인 (Timeline)]
        for i, step in enumerate(steps):
            du = str(step[3]) if len(step) > 3 else "4주"
            align_left = (i % 2 == 0)
            sh += (
                f'<div class="rv d{min(i+1,4)}" style="display:flex; justify-content:{"flex-start" if align_left else "flex-end"}; position:relative; margin-bottom:32px;">'
                f'<div style="width:calc(50% - 24px); background:var(--bg); border:1px solid var(--bd); border-radius:var(--r, 8px); padding:32px; box-shadow:0 4px 15px rgba(0,0,0,0.03); text-align:{"right" if align_left else "left"};">'
                f'<div style="font-family:var(--fh); font-size:48px; font-weight:900; color:var(--c1); line-height:1; margin-bottom:12px;">{i+1:02d}</div>'
                f'<div style="margin-bottom:12px;"><span style="font-size:10px; font-weight:800; background:var(--bg3); color:var(--text); padding:4px 12px; border-radius:100px;">{du}</span></div>'
                f'<h3 style="font-family:var(--fh); font-size:22px; font-weight:800; color:var(--text); margin-bottom:12px;">{strip_hanja(str(step[1]))}</h3>'
                f'<p style="font-size:14px; line-height:1.75; color:var(--t70); margin:0;">{strip_hanja(str(step[2]))}</p>'
                f'</div>'
                f'<div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); width:16px; height:16px; background:var(--c1); border-radius:50%; border:4px solid var(--bg2);"></div>'
                f'</div>'
            )
        return (
            f'<section class="sec alt" id="curriculum">'
            f'<div style="max-width:1000px; margin:0 auto; text-align:center;">'
            f'<div class="rv" style="margin-bottom:64px;">'
            f'<div class="tag-line" style="justify-content:center;">단계별 로드맵</div>'
            f'<h2 style="font-family:var(--fh); font-size:clamp(36px, 5vw, 56px); font-weight:900; color:var(--text); margin-bottom:16px;">{t}</h2>'
            f'<p style="font-size:16px; color:var(--t70);">{s}</p>'
            f'</div>'
            f'<div style="position:relative;">'
            f'<div style="position:absolute; top:0; bottom:0; left:50%; transform:translateX(-50%); width:2px; background:var(--bd);"></div>'
            f'{sh}'
            f'</div>'
            f'</div></section>'
        )

    else:
        # [스타일 3: 기존 스플릿 (Sticky Left) 디자인 다듬기]
        for idx, step in enumerate(steps):
            du = str(step[3]) if len(step) > 3 else "4주"
            sh += (
                f'<div class="rv d{min(idx+1,4)}" style="display:flex; gap:0; align-items:stretch; margin-bottom:16px; box-shadow:0 4px 15px rgba(0,0,0,0.02);">'
                f'<div style="flex-shrink:0; width:100px; background:{"var(--c1)" if idx%2==0 else "var(--bg3)"}; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:24px 12px; border-radius:var(--r,8px) 0 0 var(--r,8px);">'
                f'<div style="font-family:var(--fh); font-size:11px; font-weight:900; color:{"var(--bg)" if idx%2==0 else "var(--c1)"}; opacity:0.7; letter-spacing:0.1em; margin-bottom:4px;">STEP</div>'
                f'<div style="font-family:var(--fh); font-size:40px; font-weight:900; color:{"var(--bg)" if idx%2==0 else "var(--c1)"}; line-height:1;">{idx+1:02d}</div>'
                f'</div>'
                f'<div style="flex:1; padding:32px; background:var(--bg); border-radius:0 var(--r,8px) var(--r,8px) 0; border:1px solid var(--bd); border-left:none;">'
                f'<div style="display:flex; align-items:center; gap:16px; margin-bottom:12px;">'
                f'<h3 style="font-family:var(--fh); font-size:22px; font-weight:900; color:var(--text); margin:0;">{strip_hanja(str(step[1]))}</h3>'
                f'<span style="font-size:11px; background:var(--bg3); color:var(--c1); padding:4px 14px; border-radius:100px; font-weight:800; border:1px solid var(--bd); flex-shrink:0;">{du}</span>'
                f'</div>'
                f'<p style="font-size:14.5px; line-height:1.85; color:var(--t70); margin:0;">{strip_hanja(str(step[2]))}</p>'
                f'</div></div>'
            )
        return (
            f'<section class="sec alt" id="curriculum">'
            f'<div style="display:grid; grid-template-columns:1fr 1.5fr; gap:60px; align-items:start; max-width:1200px; margin:0 auto;">'
            f'<div class="rv" style="position:sticky; top:100px;">'
            f'<div class="tag-line">커리큘럼</div>'
            f'<h2 style="font-family:var(--fh); font-size:clamp(36px, 5vw, 64px); font-weight:900; color:var(--text); margin-bottom:20px; line-height:1.1;">{t}</h2>'
            f'<p style="font-size:16px; line-height:1.9; color:var(--t70); margin-bottom:40px;">{s}</p>'
            f'<div style="padding:32px; background:var(--c1); border-radius:var(--r,8px); color:var(--bg);">'
            f'<div style="font-size:12px; font-weight:800; letter-spacing:0.15em; text-transform:uppercase; opacity:0.8; margin-bottom:12px;">TOTAL DURATION</div>'
            f'<div style="font-family:var(--fh); font-size:64px; font-weight:900; line-height:1;">{len(steps)*4}주</div>'
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
    desc = strip_hanja(cp.get("eventDesc", "기간 한정 이벤트입니다."))
    details = cp.get("eventDetails", [["📅","기간","진행중"],["🎯","대상","수험생"],["💰","혜택","확인"]])
    
    dh = ""
    for i, row in enumerate(details):
        ic = str(row[0]) if len(row)>0 else "✦"
        lb = str(row[1]) if len(row)>1 else "정보"
        vl = str(row[2]) if len(row)>2 else "-"
        dh += f'<div class="card rv d{i+1}" style="text-align:center;padding:32px 20px"><div style="font-size:36px;margin-bottom:14px">{ic}</div><div style="font-size:10px;font-weight:800;color:var(--c1);letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px">{lb}</div><div style="font-family:var(--fh);font-size:19px;font-weight:700">{vl}</div></div>'
        
    return f'<section class="sec" id="event-overview"><div style="max-width:1200px;margin:0 auto"><div class="rv"><div class="tag-line">이벤트 개요</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{desc}</p></div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px">{dh}</div></div></section>'

def sec_video(d, cp, T):
    """영상 미리보기 섹션 렌더러"""
    t = strip_hanja(cp.get("videoTitle", "영상 미리보기"))
    sub = strip_hanja(cp.get("videoSub", "영상을 통해 자세한 내용을 확인하세요"))
    tag = strip_hanja(cp.get("videoTag", "OFFICIAL TRAILER"))
    
    # 사이드바에서 입력한 videoUrl 가져오기
    v_url = cp.get("videoUrl", "")
    
    if not v_url:
        video_html = (
            f'<div style="width:100%; aspect-ratio:16/9; background:var(--bg3); border-radius:var(--r, 8px); display:flex; align-items:center; justify-content:center; color:var(--t45); border:1px dashed var(--bd);">'
            f'사이드바에서 YouTube embed URL을 입력해주세요.'
            f'</div>'
        )
    else:
        video_html = (
            f'<iframe width="100%" style="aspect-ratio:16/9; border-radius:var(--r, 8px); border:none; box-shadow:0 12px 40px rgba(0,0,0,.15);" '
            f'src="{v_url}" title="YouTube video" frameborder="0" '
            f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
        )

    return (
        f'<section class="sec" id="video">'
        f'<div style="max-width:1000px; margin:0 auto; text-align:center;">'
        f'<div class="rv" style="margin-bottom:48px;">'
        f'<div class="tag-line" style="justify-content:center;">{tag}</div>'
        f'<h2 style="font-family:var(--fh); font-size:clamp(32px, 5vw, 56px); font-weight:900; color:var(--text); margin-bottom:16px;">{t}</h2>'
        f'<p style="font-size:16px; color:var(--t70);">{sub}</p>'
        f'</div>'
        f'<div class="rv d1">{video_html}</div>'
        f'</div></section>'
    )

def sec_event_benefits(d, cp, T):
    t = strip_hanja(cp.get("benefitsTitle", "이벤트 특별 혜택"))
    benefits = cp.get("eventBenefits", [{"icon":"🎁","title":"할인","desc":"혜택제공","badge":"혜택","no":"01"}])
    
    bh = ""
    for i, b in enumerate(benefits):
        if not isinstance(b, dict): continue
        icon, no = b.get("icon","✦"), b.get("no",f"{i+1:02d}")
        badge, title, desc = strip_hanja(b.get("badge","혜택")), strip_hanja(b.get("title","")), strip_hanja(b.get("desc",""))
        bh += (
            f'<div class="card rv d{min(i+1,4)}" style="display:grid;grid-template-columns:64px 1fr;gap:20px;align-items:flex-start;padding:24px">'
            f'<div style="width:64px;height:64px;border-radius:var(--r,4px);background:linear-gradient(135deg,var(--c1),var(--c2));display:flex;align-items:center;justify-content:center;font-size:28px;flex-shrink:0">{icon}</div>'
            f'<div><div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">'
            f'<span style="font-size:9px;font-weight:800;color:var(--c1);opacity:.7">NO.{no}</span>'
            f'<span style="background:var(--c1);color:#fff;font-size:9px;font-weight:800;padding:2px 10px;border-radius:100px">{badge}</span></div>'
            f'<div style="font-family:var(--fh);font-size:15px;font-weight:700;margin-bottom:7px" class="st">{title}</div>'
            f'<p style="font-size:12.5px;line-height:1.85;color:var(--t70)">{desc}</p>'
            f'</div></div>'
        )
    return f'<section class="sec alt" id="event-benefits"><div style="max-width:1200px;margin:0 auto"><div class="rv"><div class="tag-line">이벤트 혜택</div><h2 class="sec-h2 st">{t}</h2></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px">{bh}</div></div></section>'

def sec_event_deadline(d, cp, T):
    t   = strip_hanja(cp.get("deadlineTitle","마감 안내"))
    msg = strip_hanja(cp.get("deadlineMsg","기간 한정 운영됩니다."))
    cc  = strip_hanja(cp.get("ctaCopy","이벤트 신청하기"))
    return (
        f'<section id="event-deadline" style="padding:clamp(80px,10vw,120px) clamp(28px,6vw,72px);text-align:center;position:relative;overflow:hidden;background:{T["cta"]}">'
        f'<div class="rv" style="max-width:680px;margin:0 auto;position:relative;z-index:1">'
        f'<div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.15);backdrop-filter:blur(8px);padding:7px 22px;border-radius:100px;font-size:11px;font-weight:800;color:#fff;margin-bottom:24px;border:1px solid rgba(255,255,255,.25)">⏰ 마감 임박</div>'
        f'<h2 style="font-family:\'Black Han Sans\',var(--fh);font-size:clamp(28px,5vw,56px);font-weight:900;color:#fff;margin-bottom:16px">{t}</h2>'
        f'<p style="color:rgba(255,255,255,.7);font-size:15px;line-height:1.9;margin:0 auto 32px">{msg}</p>'
        f'<a style="display:inline-flex;align-items:center;background:#fff;color:#0A0A0A;font-weight:900;padding:18px 52px;border-radius:var(--r-btn,4px);font-size:17px;text-decoration:none" href="#cta">{cc} →</a>'
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
    """수강 전후 비교 — 3가지 다이내믹 레이아웃"""
    t   = strip_hanja(cp.get('baTitle', '공부 방식이 이렇게 달라집니다'))
    sub = strip_hanja(cp.get('baSub', f"{d['purpose_label']} 이후의 변화"))
    befores = cp.get('baBeforeItems', [f"{d['subject']} 지문이 무슨 말인지 몰라 다 읽는다", '시간이 부족해 뒷문제를 찍는다', '시험장에서 실수가 계속 나온다'])
    afters = cp.get('baAfterItems', ['구조가 보여서 필요한 부분만 읽는다', '시간이 남아 검토까지 완료한다', '배운 대로 정확히 풀어낸다'])
    
    v = (sum(ord(c) for c in t) % 3) + 1

    if v == 1:
        # [스타일 1: 세련된 벤토박스형 교차 배열 (Modern Grid)]
        bh_ah_combined = ""
        for i in range(min(len(befores), len(afters))):
            bh_ah_combined += (
                f'<div class="rv d{i+1}" style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px;">'
                f'<div style="background:var(--bg2); border:1px solid var(--bd); padding:24px; border-radius:var(--r,8px); display:flex; align-items:flex-start; gap:12px;">'
                f'<div style="width:24px; height:24px; border-radius:50%; background:rgba(200,50,50,0.1); color:#D32F2F; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:900; flex-shrink:0;">✕</div>'
                f'<p style="font-size:14.5px; line-height:1.7; color:var(--t70); margin:0;">{strip_hanja(befores[i])}</p>'
                f'</div>'
                f'<div style="background:var(--c1); padding:24px; border-radius:var(--r,8px); display:flex; align-items:flex-start; gap:12px; box-shadow:0 8px 20px rgba(0,0,0,0.1);">'
                f'<div style="width:24px; height:24px; border-radius:50%; background:rgba(255,255,255,0.2); color:#fff; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:900; flex-shrink:0;">✓</div>'
                f'<p style="font-size:14.5px; line-height:1.7; color:#fff; font-weight:600; margin:0;">{strip_hanja(afters[i])}</p>'
                f'</div></div>'
            )
        return (
            f'<section class="sec" id="before-after">'
            f'<div style="max-width:1000px; margin:0 auto;">'
            f'<div class="rv" style="text-align:center; margin-bottom:56px;">'
            f'<div class="tag-line" style="justify-content:center;">BEFORE & AFTER</div>'
            f'<h2 style="font-family:var(--fh); font-size:clamp(32px, 4.5vw, 56px); font-weight:900; color:var(--text); margin-bottom:16px;">{t}</h2>'
            f'<p style="font-size:16px; color:var(--t70);">{sub}</p>'
            f'</div>'
            f'<div style="display:flex; justify-content:space-between; padding:0 24px; margin-bottom:16px; font-family:var(--fh); font-weight:900; font-size:14px; color:var(--t45); letter-spacing:0.1em;">'
            f'<span>수강 전의 한계</span><span>수강 후의 변화</span></div>'
            f'<div>{bh_ah_combined}</div>'
            f'</div></section>'
        )

    elif v == 2:
        # [스타일 2: 애플 Mac 비교표 스타일 (Sleek Table)]
        rows = ""
        for i in range(min(len(befores), len(afters))):
            rows += (
                f'<div class="rv d{min(i+1,4)}" style="display:grid; grid-template-columns:1fr 40px 1fr; align-items:center; padding:24px 0; border-bottom:1px solid var(--bd);">'
                f'<div style="text-align:right; font-size:15px; color:var(--t70); padding-right:20px;">{strip_hanja(befores[i])}</div>'
                f'<div style="width:32px; height:32px; border-radius:50%; background:var(--bg3); display:flex; align-items:center; justify-content:center; color:var(--c1); font-weight:900; margin:0 auto;">›</div>'
                f'<div style="font-size:15px; font-weight:700; color:var(--text); padding-left:20px;">{strip_hanja(afters[i])}</div>'
                f'</div>'
            )
        return (
            f'<section class="sec alt" id="before-after">'
            f'<div style="max-width:900px; margin:0 auto; text-align:center;">'
            f'<div class="rv" style="margin-bottom:64px;">'
            f'<div class="tag-line" style="justify-content:center;">놀라운 변화</div>'
            f'<h2 style="font-family:var(--fh); font-size:clamp(36px, 5vw, 60px); font-weight:900; color:var(--text); margin-bottom:16px;">{t}</h2>'
            f'<p style="font-size:16px; color:var(--t70);">{sub}</p>'
            f'</div>'
            f'<div style="background:var(--bg); border:1px solid var(--bd); border-radius:var(--r,12px); padding:24px 40px; box-shadow:0 8px 30px rgba(0,0,0,0.03);">'
            f'<div style="display:grid; grid-template-columns:1fr 40px 1fr; padding-bottom:16px; border-bottom:2px solid var(--text); font-family:var(--fh); font-weight:900; font-size:18px;">'
            f'<div style="color:var(--t45); text-align:right; padding-right:20px;">BEFORE</div><div></div><div style="color:var(--c1); text-align:left; padding-left:20px;">AFTER</div>'
            f'</div>'
            f'{rows}'
            f'</div></div></section>'
        )

    else:
        # [스타일 3: 기존 다크/라이트 대조형 블록 다듬기]
        bh = "".join(
            f'<div style="display:flex;gap:12px;margin-bottom:20px;align-items:flex-start">'
            f'<div style="color:#FF5252;font-weight:900;font-size:16px;flex-shrink:0">✕</div>'
            f'<p style="font-size:14.5px;line-height:1.75;color:rgba(255,255,255,0.82);'
            f'margin:0;font-weight:500">{strip_hanja(b)}</p></div>'
            for b in befores
        )
        # ✅ after: var(--bg3) 배경이므로 var(--text) 사용
        ah = "".join(
            f'<div style="display:flex;gap:12px;margin-bottom:20px;align-items:flex-start">'
            f'<div style="color:var(--c1);font-weight:900;font-size:16px;flex-shrink:0">✓</div>'
            f'<p style="font-size:14.5px;line-height:1.75;color:var(--text);'
            f'margin:0;font-weight:600;opacity:0.85">{strip_hanja(a)}</p></div>'
            for a in afters
        )
        
        return (
            f'<section class="sec" id="before-after">'
            f'<div style="max-width:1000px;margin:0 auto;">'
            f'<div class="rv" style="text-align:center;margin-bottom:56px;">'
            f'<div class="tag-line" style="justify-content:center;">수강 전과 후</div>'
            f'<h2 style="font-family:var(--fh);font-size:clamp(32px,5vw,56px);'
            f'font-weight:900;color:var(--text);margin-bottom:16px;">{t}</h2>'
            f'<p style="font-size:16px;color:var(--text);opacity:0.65;">{sub}</p>'
            f'</div>'
            f'<div class="rv d1" style="display:grid;grid-template-columns:1fr 48px 1.2fr;'
            f'align-items:stretch;border-radius:var(--r,12px);overflow:hidden;'
            f'box-shadow:0 12px 40px rgba(0,0,0,0.15);">'
            # BEFORE 패널 — 어두운 배경, 흰 글씨
            f'<div style="background:#111111;padding:48px 40px;">'
            f'<div style="font-family:var(--fh);font-size:22px;font-weight:900;'
            f'color:rgba(255,255,255,0.4);margin-bottom:28px;letter-spacing:0.1em">BEFORE</div>'
            f'{bh}</div>'
            # 화살표
            f'<div style="background:var(--c1);display:flex;align-items:center;'
            f'justify-content:center;color:#ffffff;font-size:22px;font-weight:900;">→</div>'
            # AFTER 패널 — 밝은 배경, 어두운 글씨
            f'<div style="background:var(--bg3);padding:48px 40px;">'
            f'<div style="font-family:var(--fh);font-size:22px;font-weight:900;'
            f'color:var(--c1);margin-bottom:28px;letter-spacing:0.1em">AFTER</div>'
            f'{ah}</div>'
            f'</div></div></section>'
        )
        ah = ''.join(f'<div style="display:flex; gap:12px; margin-bottom:20px;"><div style="color:var(--c1); font-weight:900;">✓</div><p style="font-size:14.5px; line-height:1.7; color:var(--text); font-weight:600; margin:0;">{strip_hanja(a)}</p></div>' for a in afters)
        
        return (
            f'<section class="sec" id="before-after">'
            f'<div style="max-width:1000px; margin:0 auto;">'
            f'<div class="rv" style="text-align:center; margin-bottom:56px;">'
            f'<div class="tag-line" style="justify-content:center;">수강 전과 후</div>'
            f'<h2 style="font-family:var(--fh); font-size:clamp(32px, 5vw, 56px); font-weight:900; color:var(--text); margin-bottom:16px;">{t}</h2>'
            f'<p style="font-size:16px; color:var(--t70);">{sub}</p>'
            f'</div>'
            f'<div class="rv d1" style="display:grid; grid-template-columns:1fr auto 1.2fr; align-items:stretch; border-radius:var(--r,12px); overflow:hidden; box-shadow:0 12px 40px rgba(0,0,0,0.1);">'
            f'<div style="background:#111; padding:48px 40px;">'
            f'<div style="font-family:var(--fh); font-size:24px; font-weight:900; color:#fff; margin-bottom:32px;">BEFORE</div>{bh}</div>'
            f'<div style="background:var(--c1); width:48px; display:flex; align-items:center; justify-content:center; color:#fff; font-size:24px; font-weight:900;">→</div>'
            f'<div style="background:var(--bg3); padding:48px 40px;">'
            f'<div style="font-family:var(--fh); font-size:24px; font-weight:900; color:var(--c1); margin-bottom:32px;">AFTER</div>{ah}</div>'
            f'</div></div></section>'
        )


def sec_grade_stats(d, cp, T):
    """학습 변화 흐름 — 수강 전~수능 당일까지의 4단계 여정 시각화"""
    t   = strip_hanja(cp.get("gradeTitle", f"{d['purpose_label']}으로 달라지는 것들"))
    sub = strip_hanja(cp.get("gradeSub",   f"{d['subject']} 공부의 방식이 이렇게 바뀝니다"))

    # ✅ 금지된 타 커리큘럼명 필터
    _plabel = st.session_state.get("purpose_label", "")
    _BANNED_NAMES = ["인셉션", "O.V.S", "OVS", "파노라마", "뉴런", "R'gorithm",
                     "Starting Block", "KICE Anatomy", "세젤쉬", "All Of KICE",
                     "VIC-FLIX", "KISS Logic", "KISSAVE", "KISSCHEMA"]
    def _clean_card_text(text: str) -> str:
        for bn in _BANNED_NAMES:
            if bn.lower() not in _plabel.lower():
                text = text.replace(bn, _plabel if _plabel else "")
        return text

    reasons = cp.get("whyReasons", [])
    cards   = []
    for r in reasons[:3]:
        if isinstance(r, (list, tuple)) and len(r) >= 3:
            cards.append((
                str(r[0]),
                _clean_card_text(str(r[1])),
                _clean_card_text(str(r[2]))
            ))
    if not cards:
        cards = [
            ("🎯", "출제 원리 파악",  "감이 아닌 원리로 접근하면 어떤 유형도 흔들리지 않습니다"),
            ("⚡", "실전 속도 향상",  "훈련된 눈으로 지문을 읽으면 시간이 남기 시작합니다"),
            ("📊", "기출 완전 분석",  "최근 기출의 패턴을 꿰뚫으면 다음 수능이 보입니다"),
        ]

    STAGES = [
        ("수강 전",    f"{d['subject']} 공부, 어디서부터 해야 할지 막막하다",       False),
        ("1~2주차",   "개념의 틀이 잡히고 지문 구조가 보이기 시작한다",              False),
        ("3~4주차",   "기출 패턴이 눈에 익고 답이 보이는 경험을 한다",             False),
        ("수능 당일",  f"배운 대로 정확히 풀어내는 자신감으로 시험장에 들어간다",    True),
    ]

    flow_html = ""
    for i, (stage, desc, is_final) in enumerate(STAGES):
        # ✅ Python 변수로 미리 색상 결정 (f-string 안에 if 금지)
        card_bg     = "var(--c1)"    if is_final else "var(--bg3)"
        card_border = "var(--c1)"    if is_final else "var(--bd)"
        stage_col   = "rgba(255,255,255,0.6)" if is_final else "var(--c1)"
        desc_col    = "rgba(255,255,255,0.92)" if is_final else "var(--text)"
        desc_weight = "700"          if is_final else "500"
        desc_opacity= "1"            if is_final else "0.72"
        arrow_html  = (
            f'<div style="position:absolute;top:50%;right:-13px;'
            f'transform:translateY(-50%);font-size:18px;'
            f'color:var(--c1);z-index:2;font-weight:900">›</div>'
            if i < 3 else ''
        )
        flow_html += (
            f'<div class="rv d{min(i+1,4)}" '
            f'style="flex:1;min-width:150px;position:relative">'
            f'<div style="padding:24px 18px;height:100%;'
            f'background:{card_bg};'
            f'border-radius:var(--r,4px);'
            f'border:2px solid {card_border}">'
            f'<div style="font-size:9px;font-weight:800;letter-spacing:.14em;'
            f'text-transform:uppercase;color:{stage_col};margin-bottom:10px">'
            f'{stage}</div>'
            f'<p style="font-size:13px;line-height:1.75;margin:0;'
            f'font-weight:{desc_weight};'
            f'color:{desc_col};opacity:{desc_opacity}">{desc}</p>'
            f'</div>'
            + arrow_html
            + f'</div>'
        )

    card_html = "".join(
        f'<div class="card rv d{min(i+1,3)}" style="padding:28px">'
        f'<div style="font-size:36px;margin-bottom:14px">{ic}</div>'
        f'<div style="font-size:15px;font-weight:800;color:var(--text);margin-bottom:8px">'
        f'{strip_hanja(tt)}</div>'
        f'<p style="font-size:13px;line-height:1.85;color:var(--t70);margin:0">'
        f'{strip_hanja(dc)}</p>'
        f'</div>'
        for i, (ic, tt, dc) in enumerate(cards)
    )

    return (
        f'<section class="sec alt" id="grade-stats">'
        f'<div style="max-width:1100px;margin:0 auto">'
        f'<div class="rv" style="text-align:center;margin-bottom:40px">'
        f'<div class="tag-line" style="justify-content:center">학습 변화</div>'
        f'<h2 class="sec-h2 st" style="text-align:center">{t}</h2>'
        f'<p class="sec-sub" style="text-align:center;margin:0 auto">{sub}</p>'
        f'</div>'
        # 변화 흐름 타임라인
        f'<div class="rv d1" style="display:flex;gap:24px;align-items:stretch;'
        f'flex-wrap:wrap;margin-bottom:40px">{flow_html}</div>'
        # 핵심 카드
        f'<div style="display:grid;grid-template-columns:repeat({min(len(cards),3)},1fr);'
        f'gap:14px" class="rv d2">{card_html}</div>'
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
    """구매 패키지 섹션 — 세련된 다단 그리드(Bento Box) 스타일"""
    t    = strip_hanja(cp.get("pkgTitle",   f"{d['purpose_label']} 구성 안내"))
    sub  = strip_hanja(cp.get("pkgSub",     "지금 신청하면 아래 구성이 모두 포함됩니다"))
    pkgs = cp.get("packages",[
        {"icon":"📗","name":"본교재 (KEY STEP)","desc":"최신 기출 트렌드가 완벽히 반영된 메인 교재","badge":"필수"},
        {"icon":"📝","name":"워크북 (복습용)","desc":"수업 내용을 체화하고 약점을 보완하는 복습 과제장","badge":"포함"},
        {"icon":"🎯","name":"실전 하프 모의고사","desc":"매주 실전 감각을 극대화하는 미니 모의고사 3회분","badge":"포함"},
        {"icon":"💬","name":"1:1 밀착 Q&A","desc":"연구진이 직접 답변하는 프라이빗 질문 게시판","badge":"특전"},
    ])
    
    # 🌟 레이아웃을 2단 그리드 카드 형태로 고급스럽게 변경
    ph = "".join(
        f'<div class="card rv d{min(i+1,4)}" style="display:flex; flex-direction:column; justify-content:space-between; padding:32px; background:{"var(--bg)" if i%2!=0 else "var(--bg3)"}; border:1px solid var(--bd); border-radius:var(--r, 8px); height:100%; transition:transform 0.3s, box-shadow 0.3s;">'
        f'<div>'
        f'<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:24px;">'
        f'<div style="font-size:42px; line-height:1; filter:drop-shadow(0 4px 6px rgba(0,0,0,0.1));">{p.get("icon","📦") if isinstance(p,dict) else "📦"}</div>'
        + (lambda _b: f'<span style="font-size:11px; font-weight:800; background:{"var(--c1)" if _b=="필수" else "transparent"}; color:{"#fff" if _b=="필수" else "var(--t70)"}; padding:6px 14px; border-radius:var(--r-btn,100px); border:1.5px solid {"var(--c1)" if _b=="필수" else "var(--bd)"}; letter-spacing:0.05em;">{_b}</span>')(strip_hanja(str(p.get("badge","포함") if isinstance(p,dict) else "포함"))) +
        f'</div>'
        f'<h3 style="font-family:var(--fh); font-size:20px; font-weight:900; color:var(--text); margin-bottom:12px; letter-spacing:-0.02em;">{strip_hanja(str(p.get("name","") if isinstance(p,dict) else p))}</h3>'
        f'<p style="font-size:14px; line-height:1.75; color:var(--t70); margin:0; word-break:keep-all;">{strip_hanja(str(p.get("desc","") if isinstance(p,dict) else ""))}</p>'
        f'</div>'
        f'</div>'
        for i, p in enumerate(pkgs)
    )
    
    return (
        f'<section class="sec alt" id="package">'
        f'<div style="max-width:1100px; margin:0 auto;">'
        f'<div class="rv" style="text-align:center; margin-bottom:56px;">'
        f'<div class="tag-line" style="justify-content:center">패키지 구성</div>'
        f'<h2 class="sec-h2 st" style="text-align:center">{t}</h2>'
        f'<p class="sec-sub" style="text-align:center; margin:0 auto">{sub}</p>'
        f'</div>'
        f'<div class="rv d1" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:20px;">{ph}</div>'
        f'</div></section>'
    )

# ═══════════════════════════════════════════════════════
# 강좌 소개 섹션 렌더러
# ═══════════════════════════════════════════════════════
def sec_course_intro(d, cp, T):
    """강좌 소개 섹션 — 3가지 다이내믹 레이아웃 (벤토박스 / 에디토리얼 / 스플릿)"""
    c = cp.get("course_copy") or st.session_state.get("course_copy") or {}
    if not c:
        return (
            f'<section class="sec alt" id="course-intro">'
            f'<div style="max-width:900px;margin:0 auto;text-align:center;padding:40px 0">'
            f'<p style="color:var(--t45);font-size:14px">사이드바 → 강좌 정보 입력 후 "강좌 소개 생성" 버튼을 눌러주세요</p>'
            f'</div></section>'
        )

    title   = strip_hanja(c.get("courseTitle", "강좌 소개"))
    sub     = strip_hanja(c.get("courseSub", ""))
    desc    = strip_hanja(c.get("courseDesc", ""))
    points  = c.get("coursePoints", [])
    dur     = strip_hanja(c.get("courseDuration", ""))
    level   = strip_hanja(c.get("courseLevel", ""))
    tags    = [strip_hanja(t) for t in c.get("courseTag", [])]

    text_hash = sum(ord(ch) for ch in title + sub)
    v = (text_hash % 3) + 1

    # 메타 뱃지 & 태그 조립
    meta = ""
    if dur: meta += f'<span style="display:inline-flex;align-items:center;gap:6px;background:var(--bg3);padding:6px 16px;border-radius:var(--r-btn,100px);font-size:11px;font-weight:700;color:var(--text);border:1px solid var(--bd);margin-right:8px">⏱ {dur}</span>'
    if level: meta += f'<span style="display:inline-flex;align-items:center;gap:6px;background:var(--c1);padding:6px 16px;border-radius:var(--r-btn,100px);font-size:11px;font-weight:700;color:#fff;margin-right:8px">🎯 {level}</span>'
    tag_html = "".join(f'<span style="font-size:11px;font-weight:800;padding:6px 14px;border:1.5px solid var(--bd);border-radius:var(--r-btn,100px);color:var(--t70);margin-right:6px;margin-bottom:6px;display:inline-block">#{tg}</span>' for tg in tags[:4])

    if v == 1:
        # [스타일 1: 비대칭 벤토박스 (Bento Box) 레이아웃]
        ph = ""
        for i, pt in enumerate(points[:3]):
            if not isinstance(pt, dict): continue
            ph += (
                f'<div class="card rv d{i+2}" style="padding:32px; background:{"var(--bg3)" if i%2==0 else "var(--bg)"}; border-radius:var(--r, 8px); border:1px solid var(--bd);">'
                f'<div style="font-size:36px; margin-bottom:16px;">{pt.get("icon","✦")}</div>'
                f'<h4 style="font-family:var(--fh); font-size:18px; font-weight:800; color:var(--text); margin-bottom:12px;">{strip_hanja(pt.get("title",""))}</h4>'
                f'<p style="font-size:13.5px; line-height:1.8; color:var(--t70); margin:0;">{strip_hanja(pt.get("desc",""))}</p>'
                f'</div>'
            )
        
        return (
            f'<section class="sec alt" id="course-intro">'
            f'<div style="max-width:1100px; margin:0 auto">'
            f'<div class="rv d1" style="display:grid; grid-template-columns:1.2fr 1fr; gap:40px; align-items:center; margin-bottom:40px;">'
            f'<div><div class="tag-line">COURSE INFO</div>'
            f'<h2 style="font-family:var(--fh); font-size:clamp(36px, 5vw, 64px); font-weight:900; color:var(--text); letter-spacing:-0.03em; margin-bottom:16px; line-height:1.1;">{title}</h2>'
            f'<p style="font-size:16px; color:var(--t70); margin-bottom:24px; font-weight:500;">{sub}</p>'
            f'<div style="display:flex; flex-wrap:wrap; margin-bottom:16px;">{meta}</div>'
            f'<div style="display:flex; flex-wrap:wrap;">{tag_html}</div></div>'
            f'<div style="background:var(--c1); padding:40px; border-radius:var(--r, 8px); color:var(--bg);">'
            f'<div style="font-size:40px; margin-bottom:20px; opacity:0.8;">"</div>'
            f'<p style="font-size:16px; line-height:1.9; font-weight:600; margin:0;">{desc}</p>'
            f'</div></div>'
            f'<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:16px;">{ph}</div>'
            f'</div></section>'
        )

    elif v == 2:
        # [스타일 2: 에디토리얼 프리미엄 (중앙 정렬 + 거대 타이포그래피)]
        ph = ""
        for i, pt in enumerate(points[:3]):
            if not isinstance(pt, dict): continue
            ph += (
                f'<div class="rv d{i+2}" style="text-align:center; padding:24px 16px;">'
                f'<div style="width:64px; height:64px; background:var(--bg3); border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 20px; font-size:28px; border:1px solid var(--bd);">{pt.get("icon","✦")}</div>'
                f'<h4 style="font-family:var(--fh); font-size:18px; font-weight:900; color:var(--text); margin-bottom:12px;">{strip_hanja(pt.get("title",""))}</h4>'
                f'<p style="font-size:14px; line-height:1.8; color:var(--t70); margin:0;">{strip_hanja(pt.get("desc",""))}</p>'
                f'</div>'
            )
        
        return (
            f'<section class="sec" id="course-intro">'
            f'<div style="max-width:900px; margin:0 auto; text-align:center;">'
            f'<div class="rv d1">'
            f'<div class="tag-line" style="justify-content:center;">강좌 핵심 소개</div>'
            f'<h2 style="font-family:var(--fh); font-size:clamp(40px, 6vw, 72px); font-weight:900; color:var(--text); letter-spacing:-0.04em; margin-bottom:24px; line-height:1.1;">{title}</h2>'
            f'<div style="display:flex; flex-wrap:wrap; justify-content:center; gap:8px; margin-bottom:40px;">{meta}</div>'
            f'<p style="font-size:18px; line-height:1.9; color:var(--t70); margin-bottom:60px; max-width:700px; margin-left:auto; margin-right:auto;">{desc}</p>'
            f'</div>'
            f'<div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; border-top:1px solid var(--bd); padding-top:40px;">{ph}</div>'
            f'</div></section>'
        )

    else:
        # [스타일 3: 스플릿 스크롤 (Sticky Left, Scroll Right)]
        ph = ""
        for i, pt in enumerate(points):
            if not isinstance(pt, dict): continue
            ph += (
                f'<div class="rv d{min(i+1,4)}" style="display:flex; gap:24px; padding:32px; background:var(--bg); border:1px solid var(--bd); border-radius:var(--r, 8px); margin-bottom:16px; box-shadow:0 4px 20px rgba(0,0,0,0.03);">'
                f'<div style="font-size:48px; flex-shrink:0; filter:drop-shadow(0 4px 6px rgba(0,0,0,0.1));">{pt.get("icon","✦")}</div>'
                f'<div><h4 style="font-family:var(--fh); font-size:19px; font-weight:800; color:var(--text); margin-bottom:8px;">{strip_hanja(pt.get("title",""))}</h4>'
                f'<p style="font-size:14px; line-height:1.8; color:var(--t70); margin:0;">{strip_hanja(pt.get("desc",""))}</p></div>'
                f'</div>'
            )
        
        return (
            f'<section class="sec alt" id="course-intro">'
            f'<div style="display:grid; grid-template-columns:1fr 1.3fr; gap:60px; align-items:start; max-width:1200px; margin:0 auto;">'
            f'<div class="rv d1" style="position:sticky; top:100px;">'
            f'<div class="tag-line">COURSE OVERVIEW</div>'
            f'<h2 style="font-family:var(--fh); font-size:clamp(32px, 4vw, 56px); font-weight:900; color:var(--text); letter-spacing:-0.03em; margin-bottom:16px; line-height:1.15;">{title}</h2>'
            f'<p style="font-size:16px; color:var(--t70); margin-bottom:32px; font-weight:600;">{sub}</p>'
            f'<p style="font-size:14px; line-height:1.9; color:var(--t45); margin-bottom:32px;">{desc}</p>'
            f'<div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:24px;">{meta}</div>'
            f'<div style="display:flex; flex-wrap:wrap;">{tag_html}</div>'
            f'</div>'
            f'<div>{ph}</div>'
            f'</div></section>'
        )


# ═══════════════════════════════════════════════════════
# 교재 소개·판매 섹션 렌더러
# ═══════════════════════════════════════════════════════
def sec_textbook_sale(d, cp, T):
    """교재 소개·판매 섹션 — 3가지 다이내믹 프리미엄 레이아웃"""
    c = cp.get("textbook_copy") or st.session_state.get("textbook_copy") or {}
    if not c:
        return (
            f'<section class="sec alt" id="textbook-sale">'
            f'<div style="max-width:900px;margin:0 auto;text-align:center;padding:40px 0">'
            f'<p style="color:var(--t45);font-size:14px">사이드바 → 교재 정보 입력 후 "교재 소개 생성" 버튼을 눌러주세요</p>'
            f'</div></section>'
        )

    title    = strip_hanja(c.get("tbTitle", "교재 소개"))
    sub      = strip_hanja(c.get("tbSub", ""))
    desc     = strip_hanja(c.get("tbDesc", ""))
    books    = c.get("tbBooks", [])
    features = c.get("tbFeatures", [])
    buy_title = strip_hanja(c.get("tbBuyTitle", "지금 바로 구매하기"))
    buy_desc  = strip_hanja(c.get("tbBuyDesc", ""))

    BADGE_COLORS = {
        "필수": ("var(--c1)", "var(--bg)"),
        "추천": ("var(--bg3)", "var(--c1)"),
        "심화": ("var(--bg2)", "var(--t70)"),
    }
    BOOK_EMOJIS = ["📗","📘","📙","📕","📓","📔"]

    text_hash = sum(ord(ch) for ch in title + sub)
    v = (text_hash % 3) + 1

    if v == 1:
        # [스타일 1: 다크 모드 팝아웃 (강렬한 대비)]
        book_html = ""
        for i, bk in enumerate(books[:4]):
            if not isinstance(bk, dict): continue
            bg_c, tx_c = BADGE_COLORS.get(strip_hanja(bk.get("badge","필수")), ("var(--c1)", "var(--bg)"))
            book_html += (
                f'<div class="rv d{i+2}" style="background:#111; border:1px solid #333; border-radius:var(--r,8px); padding:32px; text-align:center; position:relative; overflow:hidden;">'
                f'<div style="position:absolute; top:-20px; left:-20px; font-size:120px; opacity:0.05; filter:grayscale(100%);">{BOOK_EMOJIS[i % len(BOOK_EMOJIS)]}</div>'
                f'<div style="font-size:48px; margin-bottom:20px; position:relative; z-index:1; filter:drop-shadow(0 10px 15px rgba(0,0,0,0.5));">{BOOK_EMOJIS[i % len(BOOK_EMOJIS)]}</div>'
                f'<span style="display:inline-block; font-size:10px; font-weight:800; background:{bg_c}; color:{tx_c}; padding:4px 12px; border-radius:100px; margin-bottom:12px; position:relative; z-index:1;">{strip_hanja(bk.get("badge","필수"))}</span>'
                f'<h4 style="font-family:var(--fh); font-size:18px; font-weight:900; color:#fff; margin-bottom:12px; position:relative; z-index:1;">{strip_hanja(bk.get("name",""))}</h4>'
                f'<p style="font-size:13px; line-height:1.7; color:#aaa; margin:0; position:relative; z-index:1;">{strip_hanja(bk.get("desc",""))}</p>'
                f'</div>'
            )
        
        feat_html = "".join(f'<span style="display:inline-flex; align-items:center; gap:8px; background:rgba(255,255,255,0.1); padding:8px 20px; border-radius:100px; font-size:13px; font-weight:600; color:#eee; border:1px solid rgba(255,255,255,0.2);"><span style="font-size:16px;">{ft.get("icon","✦")}</span>{strip_hanja(ft.get("feature",""))}</span>' for ft in features if isinstance(ft, dict))

        return (
            f'<section class="sec" id="textbook-sale" style="background:#050505; color:#fff;">'
            f'<div style="max-width:1100px; margin:0 auto;">'
            f'<div class="rv d1" style="text-align:center; margin-bottom:56px;">'
            f'<div class="tag-line" style="color:var(--c1); justify-content:center;">TEXTBOOK & MATERIALS</div>'
            f'<h2 style="font-family:var(--fh); font-size:clamp(32px, 5vw, 56px); font-weight:900; color:#fff; margin-bottom:16px; letter-spacing:-0.03em;">{title}</h2>'
            f'<p style="font-size:16px; color:#888; max-width:600px; margin:0 auto;">{desc}</p>'
            f'</div>'
            f'<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:16px; margin-bottom:48px;">{book_html}</div>'
            f'<div class="rv d3" style="display:flex; flex-wrap:wrap; justify-content:center; gap:12px; margin-bottom:56px;">{feat_html}</div>'
            f'<div class="rv d4" style="text-align:center; padding:48px; background:linear-gradient(135deg, #111, #0a0a0a); border-radius:var(--r, 8px); border:1px solid #222;">'
            f'<h3 style="font-family:var(--fh); font-size:24px; font-weight:900; color:#fff; margin-bottom:12px;">{buy_title}</h3>'
            f'<p style="font-size:14px; color:#888; margin-bottom:24px;">{buy_desc}</p>'
            f'<a class="btn-p" href="#cta" style="font-size:15px; padding:16px 48px; box-shadow:0 10px 30px rgba(0,0,0,0.5);">교재 패키지 구매하기 →</a>'
            f'</div>'
            f'</div></section>'
        )

    elif v == 2:
        # [스타일 2: 카탈로그형 좌우 스플릿 (Editorial Catalog)]
        book_html = ""
        for i, bk in enumerate(books):
            if not isinstance(bk, dict): continue
            bg_c, tx_c = BADGE_COLORS.get(strip_hanja(bk.get("badge","필수")), ("var(--bg3)", "var(--c1)"))
            book_html += (
                f'<div class="rv d{min(i+1,4)}" style="display:flex; gap:20px; align-items:center; padding:24px 0; border-bottom:1px solid var(--bd);">'
                f'<div style="font-size:48px; filter:drop-shadow(0 8px 12px rgba(0,0,0,0.1));">{BOOK_EMOJIS[i % len(BOOK_EMOJIS)]}</div>'
                f'<div style="flex:1;">'
                f'<div style="display:flex; align-items:center; gap:12px; margin-bottom:6px;">'
                f'<h4 style="font-family:var(--fh); font-size:18px; font-weight:900; color:var(--text); margin:0;">{strip_hanja(bk.get("name",""))}</h4>'
                f'<span style="font-size:10px; font-weight:800; background:{bg_c}; color:{tx_c}; padding:4px 10px; border-radius:4px;">{strip_hanja(bk.get("badge","필수"))}</span>'
                f'</div>'
                f'<p style="font-size:13.5px; line-height:1.7; color:var(--t70); margin:0;">{strip_hanja(bk.get("desc",""))}</p>'
                f'</div></div>'
            )
        
        feat_html = "".join(f'<div style="display:flex; align-items:center; gap:12px; margin-bottom:16px;"><div style="width:32px; height:32px; background:var(--bg3); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:16px;">{ft.get("icon","✦")}</div><span style="font-size:14.5px; font-weight:600; color:var(--text);">{strip_hanja(ft.get("feature",""))}</span></div>' for ft in features if isinstance(ft, dict))

        return (
            f'<section class="sec" id="textbook-sale">'
            f'<div style="display:grid; grid-template-columns:1fr 1.2fr; gap:60px; max-width:1100px; margin:0 auto;">'
            f'<div class="rv d1" style="padding-right:20px;">'
            f'<div class="tag-line">교재 안내</div>'
            f'<h2 style="font-family:var(--fh); font-size:clamp(32px, 4vw, 56px); font-weight:900; color:var(--text); margin-bottom:20px; line-height:1.2;">{title}</h2>'
            f'<p style="font-size:15px; line-height:1.9; color:var(--t70); margin-bottom:40px;">{desc}</p>'
            f'<div style="padding:28px; background:var(--bg2); border-radius:var(--r,8px); margin-bottom:40px;">'
            f'<div style="font-size:11px; font-weight:800; color:var(--c1); margin-bottom:20px; letter-spacing:0.1em;">KEY FEATURES</div>'
            f'{feat_html}</div>'
            f'<div style="padding-top:32px; border-top:2px solid var(--text);">'
            f'<h3 style="font-family:var(--fh); font-size:22px; font-weight:900; color:var(--text); margin-bottom:8px;">{buy_title}</h3>'
            f'<p style="font-size:13px; color:var(--t70); margin-bottom:24px;">{buy_desc}</p>'
            f'<a class="btn-p" href="#cta" style="width:100%; justify-content:center; padding:18px;">교재 신청하기</a>'
            f'</div></div>'
            f'<div class="rv d2" style="background:var(--bg3); padding:40px; border-radius:var(--r,8px); border:1px solid var(--bd);">{book_html}</div>'
            f'</div></section>'
        )

    else:
        # [스타일 3: 가로 스크롤 카드형 (심플 & 모던)]
        book_html = ""
        for i, bk in enumerate(books):
            if not isinstance(bk, dict): continue
            bg_c, tx_c = BADGE_COLORS.get(strip_hanja(bk.get("badge","필수")), ("var(--bg3)", "var(--text)"))
            book_html += (
                f'<div class="rv d{min(i+1,4)}" style="min-width:280px; flex:1; background:var(--bg); border:1px solid var(--bd); border-radius:var(--r,8px); padding:32px 24px; text-align:center; box-shadow:0 8px 24px rgba(0,0,0,0.04);">'
                f'<div style="display:inline-flex; align-items:center; justify-content:center; width:80px; height:80px; background:var(--bg3); border-radius:50%; margin-bottom:24px; font-size:40px;">{BOOK_EMOJIS[i % len(BOOK_EMOJIS)]}</div>'
                f'<div style="margin-bottom:16px;"><span style="font-size:10px; font-weight:800; background:{bg_c}; color:{tx_c}; padding:4px 12px; border-radius:100px; border:1px solid var(--bd);">{strip_hanja(bk.get("badge","필수"))}</span></div>'
                f'<h4 style="font-family:var(--fh); font-size:18px; font-weight:800; color:var(--text); margin-bottom:12px;">{strip_hanja(bk.get("name",""))}</h4>'
                f'<p style="font-size:13px; line-height:1.7; color:var(--t70); margin:0;">{strip_hanja(bk.get("desc",""))}</p>'
                f'</div>'
            )

        feat_html = "".join(f'<div style="display:flex; flex-direction:column; align-items:center; text-align:center; padding:24px;"><div style="font-size:32px; margin-bottom:12px;">{ft.get("icon","✦")}</div><div style="font-size:14px; font-weight:700; color:var(--text);">{strip_hanja(ft.get("feature",""))}</div></div>' for ft in features if isinstance(ft, dict))

        return (
            f'<section class="sec alt" id="textbook-sale">'
            f'<div style="max-width:1200px; margin:0 auto;">'
            f'<div class="rv d1" style="text-align:center; margin-bottom:48px;">'
            f'<div class="tag-line" style="justify-content:center;">교재 구성</div>'
            f'<h2 style="font-family:var(--fh); font-size:clamp(32px, 5vw, 56px); font-weight:900; color:var(--text); margin-bottom:16px; letter-spacing:-0.03em;">{title}</h2>'
            f'<p style="font-size:16px; color:var(--t70); margin-bottom:48px;">{sub}</p>'
            f'</div>'
            f'<div style="display:flex; gap:16px; overflow-x:auto; padding-bottom:24px; scrollbar-width:none; -ms-overflow-style:none;">{book_html}</div>'
            f'<div class="rv d3" style="display:grid; grid-template-columns:repeat(3, 1fr); gap:16px; background:var(--bg); border:1px solid var(--bd); border-radius:var(--r,8px); margin-top:32px; margin-bottom:48px;">{feat_html}</div>'
            f'<div class="rv d4" style="text-align:center; padding:40px; background:var(--bg3); border-radius:var(--r,8px);">'
            f'<h3 style="font-family:var(--fh); font-size:22px; font-weight:900; color:var(--text); margin-bottom:12px;">{buy_title}</h3>'
            f'<p style="font-size:14px; color:var(--t70); margin-bottom:24px;">{buy_desc}</p>'
            f'<a class="btn-p" href="#cta" style="font-size:15px; padding:16px 40px;">지금 신청하기 →</a>'
            f'</div>'
            f'</div></section>'
        )


# ═══════════════════════════════════════════════════════
# 강사 철학 섹션 렌더러 (보너스)
# ═══════════════════════════════════════════════════════
def sec_instructor_philosophy(d, cp, T):
    """강사 철학 — 서사형 풀와이드 섹션"""
    ip = st.session_state.get("inst_profile") or {}
    plabel = st.session_state.get("purpose_label", "")
    name   = d.get("name","")

    # ── 브랜드명과 무관한 시그니처 메서드 차단 ──
    raw_methods = [m for m in (ip.get("signatureMethods") or []) if m and m != "없음"]
    if plabel and raw_methods:
        plabel_clean = plabel.replace(" ", "").lower()
        method_match = any(
            m.replace(" ", "").lower() in plabel_clean or
            plabel_clean in m.replace(" ", "").lower()
            for m in raw_methods
        )
        if not method_match:
            # 브랜드명과 무관 → 슬로건/설명도 차단
            ip = {}  # 빈 dict로 덮어씌워 모든 누수 차단

    slogan = strip_hanja(ip.get("slogan",""))
    desc   = strip_hanja(ip.get("desc",""))
    style  = strip_hanja(ip.get("teachingStyle",""))
    methods = [strip_hanja(m) for m in (ip.get("signatureMethods") or []) if m and m != "없음"]

    if not slogan and not desc:
        return ""

    ptype = st.session_state.get("purpose_type", "신규 커리큘럼")
    purpose_label = st.session_state.get("purpose_label", "")
    if ptype == "신규 커리큘럼" and purpose_label:
        # 신규 커리큘럼이면 강의 브랜드명(강좌명)을 핵심 공식으로 사용
        method_flow = purpose_label
    elif methods: # <--- 💡 여기에 있던 'sig' 오타를 'methods'로 고쳤습니다!
        method_flow = " → ".join(methods[:3])
    else:
        method_flow = f"{d['subject']} 완성"
        
    return (
        f'<section class="sec" id="instructor-philosophy" '
        f'style="background:var(--bg);overflow:hidden;position:relative">'
        # 배경 데코
        f'<div style="position:absolute;top:-100px;right:-100px;width:500px;height:500px;'
        f'border-radius:50%;background:var(--c1);opacity:.03;pointer-events:none"></div>'
        f'<div style="max-width:900px;margin:0 auto;position:relative;z-index:1">'
        # 큰 따옴표 + 슬로건
        f'<div class="rv" style="text-align:center;margin-bottom:48px">'
        f'<div style="font-size:80px;line-height:1;color:var(--c1);opacity:.2;'
        f'font-family:var(--fh);margin-bottom:-20px">"</div>'
        f'<p style="font-size:clamp(20px,3vw,32px);font-weight:800;line-height:1.5;'
        f'color:var(--text);font-style:italic;margin-bottom:20px">{slogan}</p>'
        f'<div style="display:flex;align-items:center;justify-content:center;gap:10px">'
        f'<div style="width:40px;height:2px;background:var(--c1)"></div>'
        f'<span style="font-size:12px;font-weight:700;color:var(--c1);'
        f'letter-spacing:.12em">{name} 선생님</span>'
        f'<div style="width:40px;height:2px;background:var(--c1)"></div>'
        f'</div></div>'
        # 철학 상세
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px" class="rv d1">'
        f'<div style="padding:28px;border:1px solid var(--bd);border-radius:var(--r,4px)'
        f';border-left:4px solid var(--c1)">'
        f'<div style="font-size:10px;font-weight:800;color:var(--c1);'
        f'letter-spacing:.14em;text-transform:uppercase;margin-bottom:12px">강의 철학</div>'
        f'<p style="font-size:14px;line-height:1.9;color:var(--t70)">{desc}</p>'
        f'</div>'
        f'<div style="padding:28px;border:1px solid var(--bd);border-radius:var(--r,4px)">'
        f'<div style="font-size:10px;font-weight:800;color:var(--c1);'
        f'letter-spacing:.14em;text-transform:uppercase;margin-bottom:12px">학습 방법론</div>'
        f'<p style="font-size:14px;line-height:1.9;color:var(--t70)">{style}</p>'
        f'<div style="margin-top:16px;padding:12px 16px;background:var(--bg3);'
        f'border-radius:var(--r,4px)">'
        f'<div style="font-size:11px;font-weight:800;color:var(--c1);margin-bottom:6px">핵심 공식</div>'
        f'<div style="font-family:var(--fh);font-size:15px;font-weight:900;'
        f'color:var(--text)">{method_flow}</div>'
        f'</div></div>'
        f'</div>'
        f'</div></section>'
    )

# ══════════════════════════════════════════════════════
# HTML 빌더
# ══════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════
# 섹션 사이 사선 구분선 헬퍼
# ══════════════════════════════════════════════════════
def _with_divider(html: str, idx: int, dark: bool) -> str:
    if idx == 0:
        return html
    direction = "polygon(0 0,100% 4%,100% 100%,0 100%)" if idx % 2 == 0 else "polygon(0 4%,100% 0,100% 100%,0 100%)"
    fill = "var(--bg2)" if dark else "var(--bg)"
    divider = (
        f'<div style="height:48px;background:{fill};'
        f'clip-path:{direction};margin-top:-24px;position:relative;z-index:3"></div>'
    )
    return divider + html


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
        "course_intro": sec_course_intro,             # ← 추가
        "textbook_sale": sec_textbook_sale,           # ← 추가
        "instructor_philosophy": sec_instructor_philosophy,  # ← 추가
    }
    # 네비게이션 섹션 레이블 맵
    NAV_LABELS = {
        "banner":"홈","intro":"강사 소개","why":"수강 이유",
        "curriculum":"커리큘럼","target":"수강 대상","reviews":"수강평",
        "faq":"FAQ","cta":"수강신청",
        "video":"미리보기","before_after":"수강 전/후","method":"학습법","package":"구성",
        "event_overview":"이벤트","event_benefits":"혜택","event_deadline":"마감",
        "fest_hero":"기획전","fest_lineup":"라인업","fest_benefits":"혜택","fest_cta":"신청",
        "course_intro": "강좌소개",          # ← 추가
        "textbook_sale": "교재",             # ← 추가
        "instructor_philosophy": "강사철학",  # ← 추가
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
    
    sections_html = []
    for i, s in enumerate(secs):
        if s in mp:
            sec_html = mp[s](d, cp, T)
            sections_html.append(_with_divider(sec_html, i, T["dark"]))
    body = nav_html + "\n".join(sections_html)
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
    + f'document.querySelectorAll(".reveal-text").forEach(el=>ro.observe(el));'
    + f'</script>'
    + f'<button id="mode-toggle" onclick="(function(){{var b=document.body;b.classList.toggle(\'light-mode\');localStorage.setItem(\'mode\',b.classList.contains(\'light-mode\')?\' light\':\'dark\');this.textContent=b.classList.contains(\'light-mode\')?\'🌙\':\'☀️\'}}).call(this)" title="다크/라이트 모드">☀️</button>'
    + f'<script>(function(){{var m=localStorage.getItem(\'mode\');var btn=document.getElementById(\'mode-toggle\');if(m===\'light\'){{document.body.classList.add(\'light-mode\');if(btn)btn.textContent=\'🌙\'}}}})()</script>'
    + f'<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>'
    + f'<button onclick="html2canvas(document.body).then(canvas => {{ let a = document.createElement(\'a\'); a.href = canvas.toDataURL(\'image/png\'); a.download = \'landing_page.png\'; a.click(); }})" style="position:fixed; bottom:100px; left:24px; z-index:9999; padding:14px 24px; background:#FF2244; color:#fff; border:none; border-radius:50px; font-weight:900; font-size:16px; cursor:pointer; box-shadow:0 8px 24px rgba(255,34,68,0.4);">📸 전체 화면 이미지로 저장</button>'
    + f'</body></html>'
)

# ══════════════════════════════════════════════════════
# UI CSS (사이드바 + 메인)
# ══════════════════════════════════════════════════════
st.markdown("""<style>
[data-testid="stSidebar"] {background:#07080F; border-right:1px solid #161A28;}
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p,
[data-testid="stSidebar"] span:not(.stCheckbox span),
[data-testid="stSidebar"] .stCaption {color:#8A9AB8 !important; font-size:12px !important;}
[data-testid="stSidebar"] h3 {color:#E0E8F8 !important; font-size:16px !important; font-weight:800 !important;}
[data-testid="stSidebar"] hr {border-color:#171D2F !important;}

/* 입력창 글씨 하얗게 보이게 만들기 */
[data-testid="stSidebar"] input, 
[data-testid="stSidebar"] textarea, 
[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background-color: #1A2038 !important; 
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: 1px solid #343C58 !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] input::placeholder,
[data-testid="stSidebar"] textarea::placeholder {
    color: #8A9AB8 !important;
    -webkit-text-fill-color: #8A9AB8 !important;
}

/* 드롭다운(팝업) UI 완벽 해결 */
div[data-baseweb="popover"],
div[data-baseweb="popover"] > div,
div[data-baseweb="popover"] ul {
    background-color: #1A2038 !important;
    border-color: #343C58 !important;
}
div[data-baseweb="popover"] li {
    color: #FFFFFF !important;
    background-color: transparent !important;
    font-size: 13px !important;
}
div[data-baseweb="popover"] li:hover, 
div[data-baseweb="popover"] li[aria-selected="true"] {
    background-color: #FF6B35 !important;
    color: #FFFFFF !important;
}

/* 멀티셀렉트(섹션 순서) 태그 칩 */
span[data-baseweb="tag"] {
  background-color: #232A40 !important;
  color: #FFFFFF !important;
  border: 1px solid #343C58 !important;
  border-radius: 6px !important;
  padding: 4px 10px !important;
}

.stButton>button {border-radius:6px !important; font-weight:700 !important;
  border:1px solid #232A40 !important; background:#0D1220 !important; color:#8A9AB8 !important;
  transition:all .15s !important; font-size:12px !important;}
.stButton>button:hover {background:#161E38 !important; color:#C0CDE8 !important;}
.stButton>button[kind="primary"] {background:linear-gradient(135deg,#FF6B35,#E84393) !important;
  color:#fff !important; border:none !important;}
.sec-hdr {font-size:9.5px; font-weight:800; letter-spacing:.14em; text-transform:uppercase; color:#3A4868; padding:10px 16px 5px;}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    # ─── 강좌·교재 정보 입력 ──────────────────────────
    st.markdown('<div class="sec-hdr">📖 강좌·교재 정보 입력</div>',
                unsafe_allow_html=True)
    st.caption("직접 입력하면 AI가 소개 문구를 만들어 드립니다")

    # 강좌 정보
    course_in = st.text_area(
        "강좌 정보",
        value=st.session_state.course_info,
        height=100,
        placeholder=(
            "예시:\n"
            "강좌명: 2027 뉴런 수학1\n"
            "수강 기간: 6개월\n"
            "수준: 고3·N수 중상위권\n"
            "특징: 개념-문제 괴리 해결, 총 120강"
        ),
        label_visibility="collapsed"
    )
    st.session_state.course_info = course_in

    if st.button("✦ 강좌 소개 AI 생성", use_container_width=True,
                 key="gen_course"):
        if not course_in.strip():
            st.warning("강좌 정보를 입력해주세요")
        elif not st.session_state.api_key:
            st.warning("API 키가 필요합니다")
        else:
            with st.spinner("강좌 소개 생성 중..."):
                try:
                    r = gen_course_copy(course_in)
                    st.session_state.course_copy = r
                    if st.session_state.custom_copy is None:
                        st.session_state.custom_copy = {}
                    st.session_state.custom_copy["course_copy"] = r
                    st.success("✓ 강좌 소개 생성 완료!")
                    st.rerun()
                except Exception as e:
                    st.error(f"실패: {e}")

    st.markdown("---")

    # 교재 정보
    textbook_in = st.text_area(
        "교재 정보",
        value=st.session_state.textbook_info,
        height=120,
        placeholder=(
            "예시:\n"
            "교재명: 수분감 시리즈\n"
            "구성: 수분감 기본편, 수분감 심화편\n"
            "특징: EBS 연계 분석, 핵심 유형만 수록\n"
            "가격: 각 28,000원"
        ),
        label_visibility="collapsed"
    )
    st.session_state.textbook_info = textbook_in

    if st.button("✦ 교재 소개 AI 생성", use_container_width=True,
                 key="gen_textbook"):
        if not textbook_in.strip():
            st.warning("교재 정보를 입력해주세요")
        elif not st.session_state.api_key:
            st.warning("API 키가 필요합니다")
        else:
            with st.spinner("교재 소개 생성 중..."):
                try:
                    r = gen_textbook_copy(textbook_in)
                    st.session_state.textbook_copy = r
                    if st.session_state.custom_copy is None:
                        st.session_state.custom_copy = {}
                    st.session_state.custom_copy["textbook_copy"] = r
                    st.success("✓ 교재 소개 생성 완료!")
                    st.rerun()
                except Exception as e:
                    st.error(f"실패: {e}")

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
            colors = THEME_PREVIEW_COLORS.get(k, [])
            dot = "".join(
                f'<span style="display:inline-block;width:8px;height:8px;'
                f'border-radius:50%;background:{c};margin-right:2px"></span>'
                for c in colors[:2]
            ) if colors else ""
            btn_label = t["label"]
            if st.button(btn_label, key=f"th_{k}",
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
    st.markdown('<div class="sec-hdr">🎭 카피 어조 (AI 페르소나)</div>', unsafe_allow_html=True)
    tone_options = list(COPY_TONES.keys())
    
    # 🌟 [에러 방지 안전장치] 옛날 데이터가 남아있어서 리스트에 없으면 첫 번째 값으로 초기화 🌟
    if st.session_state.copy_tone not in tone_options:
        st.session_state.copy_tone = tone_options[0]
        
    selected_tone = st.selectbox("어조 선택", tone_options,
        index=tone_options.index(st.session_state.copy_tone),
        label_visibility="collapsed")
        
    if selected_tone != st.session_state.copy_tone:
        st.session_state.copy_tone = selected_tone
        st.rerun()
        
    st.info(COPY_TONES[st.session_state.copy_tone], icon="💡")
    st.divider()
    st.markdown('<div class="sec-hdr">👤 강사 정보</div>', unsafe_allow_html=True)
    known_names = ["직접 입력"] + list(INSTRUCTOR_DB.keys())
    quick_sel = st.selectbox(
        "알려진 강사 빠른 선택",
        known_names,
        index=0,
        label_visibility="collapsed",
        key="quick_instructor"
    )
    if quick_sel != "직접 입력" and quick_sel != st.session_state.instructor_name:
        st.session_state.instructor_name = quick_sel
        info = INSTRUCTOR_DB[quick_sel]
        st.session_state.subject = info["subject"]
        st.session_state.inst_profile = info
        st.rerun()
    nm = st.text_input("강사명", value=st.session_state.instructor_name,
                   placeholder="강사명", label_visibility="collapsed")

    # ✅ 강사명 바뀌면 이전 프로필 즉시 삭제
    if nm != st.session_state.instructor_name:
        st.session_state.instructor_name = nm
        st.session_state.inst_profile = None
        st.rerun()
        st.session_state.inst_profile = None  # ← 핵심: 이전 강사 정보 초기화
        st.rerun()

    sb = st.selectbox("과목", ["영어", "수학", "국어", "사회", "과학"],
                      index=["영어","수학","국어","사회","과학"].index(st.session_state.subject),
                      label_visibility="collapsed")
    st.session_state.subject = sb

    # ✅ 추가: 강사 정보 초기화 버튼
    if st.session_state.get("inst_profile"):
        st.warning(f"⚠️ 현재 프로필: {st.session_state.inst_profile.get('bio','')[:30]}...")
        if st.button("🗑 강사 정보 초기화", use_container_width=True, key="clear_inst"):
            st.session_state.inst_profile = None
            st.session_state.instructor_name = ""
            st.rerun()

    if st.button("🔍 강사 정보 자동 검색", use_container_width=True):
        if not nm:
            st.warning("강사명을 입력해주세요")
        elif not st.session_state.api_key:
            st.warning("API 키를 입력해주세요")
        else:
            with st.spinner(f"{nm} 선생님 정보 검색 중..."):
                try:
                    p = search_instructor_improved(nm, sb)
                    st.session_state.inst_profile = p
                    if p.get("found"):
                        st.success(f"✓ {nm} 선생님 정보 검색 완료!")
                    else:
                        st.info("정보를 찾지 못했습니다.")
                except Exception as e:
                    st.error(f"검색 실패: {e}")
    st.divider()

    # 설정
    st.markdown('<div class="sec-hdr">📝 기획 방향 설정</div>', unsafe_allow_html=True)
    pl = st.text_input("브랜드명", value=st.session_state.purpose_label,
                   placeholder="2026 수능 파이널 완성", label_visibility="collapsed")

    # ✅ 브랜드명 바뀌면 생성된 문구도 초기화 (이전 강좌 내용 방지)
    if pl != st.session_state.purpose_label:
        st.session_state.purpose_label = pl
        st.session_state.custom_copy = None  # 이전 문구 초기화
        st.rerun()
    mt = st.text_input("핵심 메타포 (선택)", value=st.session_state.get("metaphor", ""),
                       placeholder="예: Surfing, Racing, 등대, 해부학",
                       help="기획안 전체를 관통하는 비유적 표현을 입력하면 카피와 시각적 디렉션에 반영됩니다.")
    st.session_state.metaphor = mt
    st.markdown('<div class="sec-hdr">🎯 수강 대상</div>', unsafe_allow_html=True)
    tgt = st.radio("대상", ["고3·N수","고1·2 — 기초 완성"], horizontal=True, label_visibility="collapsed")
    st.session_state.target = tgt
    st.divider()

    # 섹션 ON/OFF
    st.markdown('<div class="sec-hdr">📑 섹션 ON/OFF</div>', unsafe_allow_html=True)
    # 섹션 순서 및 ON/OFF (체크박스 대신 멀티셀렉트 사용)
    default_secs = PURPOSE_SECTIONS[st.session_state.purpose_type]
    
    st.session_state.active_sections = st.multiselect(
        "표시할 섹션을 원하는 순서대로 고르세요",
        options=list(SEC_LABELS.keys()),
        default=default_secs,
        format_func=lambda x: SEC_LABELS.get(x, x)
    )

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
                warns = validate_copy(st.session_state.custom_copy)
                for w in warns:
                    st.warning(w)
                st.rerun() # <--- 화면을 즉시 새로고침하는 마법의 주문!

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
    'banner':'배너', 'intro':'강좌소개', 'why':'수강이유', 'curriculum':'커리큘럼',
    'target':'수강대상', 'reviews':'수강평', 'faq':'FAQ', 'cta':'신청버튼',
    'video':'영상', 'before_after':'전후비교', 'method':'학습법', 'package':'구성안내',
    'event_overview':'이벤트개요', 'event_benefits':'이벤트혜택', 'event_deadline':'마감안내',
    'fest_hero':'기획전히어로', 'fest_lineup':'강사라인업', 'fest_benefits':'기획전혜택',
    'fest_cta':'기획전신청',
    'grade_stats':'학습효과', 'instructor_philosophy':'강사철학',
    'course_intro':'강좌소개2', 'textbook_sale':'교재소개',
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
        st.markdown("### 📋 SB 텍스트 & 디렉션 추출")
    st.caption("스토리보드에 복사/붙여넣기 편하도록 텍스트만 모아 보여줍니다.")
    if st.session_state.custom_copy:
        with st.expander("📝 SB 데이터 전체 보기 및 복사", expanded=False):
            st.info("💡 팁: 아래 텍스트 블록 우측 상단의 '복사' 아이콘을 누르면 전체 내용을 SB로 가져갈 수 있습니다.")
            
            # JSON을 기획자가 읽기 편한 텍스트로 변환하여 출력
            sb_text = ""
            cp_data = st.session_state.custom_copy
            
            if "bannerTitle" in cp_data:
                sb_text += f"[메인 배너 (Hero)]\n"
                sb_text += f"• 서브: {cp_data.get('bannerSub', '')}\n"
                sb_text += f"• 메인 카피: {cp_data.get('bannerTitle', '')}\n"
                sb_text += f"• 리드 카피: {cp_data.get('bannerLead', '')}\n"
                if cp_data.get('bannerVisual'):
                    sb_text += f"🎥 Visual Directing: {cp_data.get('bannerVisual')}\n"
                sb_text += "\n"
                
            if "introTitle" in cp_data:
                sb_text += f"[강사 소개 (Intro)]\n"
                sb_text += f"• 제목: {cp_data.get('introTitle', '')}\n"
                sb_text += f"• 본문: {cp_data.get('introDesc', '')}\n"
                if cp_data.get('introVisual'):
                    sb_text += f"🎥 Visual Directing: {cp_data.get('introVisual')}\n"
                sb_text += "\n"
                
            if "whyReasons" in cp_data:
                sb_text += f"[수강 이유 (Why)]\n"
                sb_text += f"• 제목: {cp_data.get('whyTitle', '')} / {cp_data.get('whySub', '')}\n"
                if cp_data.get('whyVisual'):
                    sb_text += f"🎥 Visual Directing: {cp_data.get('whyVisual')}\n"
                for r in cp_data.get("whyReasons", []):
                    if len(r) >= 3:
                        sb_text += f"  - [{r[0]}] {r[1]}: {r[2]}\n"
                sb_text += "\n"
                
            # 나머지 데이터는 그대로 출력
            sb_text += "[기타 데이터]\n"
            import json
            other_data = {k:v for k,v in cp_data.items() if k not in ["bannerTitle","bannerSub","bannerLead","bannerVisual","introTitle","introDesc","introVisual","whyTitle","whySub","whyReasons","whyVisual"]}
            sb_text += json.dumps(other_data, ensure_ascii=False, indent=2)

            st.code(sb_text, language="markdown")
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
    
    # 모바일/PC 전환 토글 버튼 만들기
    view_mode = st.radio("화면 크기", ["💻 PC 화면", "📱 모바일 화면"], horizontal=True)
    
    preview_width = 400 if view_mode == "📱 모바일 화면" else None

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
    components.html(final_html, height=preview_height, width=preview_width, scrolling=True)
