"""
강사 페이지 빌더 Pro v14 — 실무용 정리판
[v15] ✨ 시안형: CMS 삽입용 코드(CSS 범위 제한·이미지 자리표시) / Pretendard 기본 서체 / 고정 메뉴바 / 수강 대상 섹션 / 상투어 금지 강화
[v14] ✨ 시안형: 모든 섹션을 먼저 펼쳐 놓고 순서·표시를 직접 고르기 / 핵심 문구 후보 3개 + 디렉터 선택(카피 워크숍)
[v10] ✨ 시안형 PR 페이지 모드: 컨셉 키트 + 블록 구성 + 스타일 팩 (실제 PR 시안 문법)
[v9] 📝 강좌 특징 HTML 모드 추가: 원고 → 관리자 페이지용 인라인 CSS HTML(.txt) + 미리보기(.html)
[문구]
- 날짜는 코드가 계산(기준 수능·시즌). D-day 숫자는 100일 이내 + 사이드바 허용 시에만
- 실제 대성마이맥 PR 페이지 문법(킥커 → 워드마크 → 설명 / 학생 장면형 헤드라인)으로 프롬프트 재작성
- 생성 후 품질 검사(근거 없는 날짜·수치·상투어) → 위반 필드만 1회 자동 재작성
- gpt-oss 모델 파라미터 버그 수정(그동안 매번 실패하고 백업 모델로 넘어가던 문제)
[디자인]
- 한글 Pretendard 통일, 테마 폰트는 워드마크·영문 라벨 전용
- 랜덤 레이아웃·마키·워터마크·사선 구분선·플로팅 버튼 제거 → 고정된 섹션 리듬
- 히어로 키비주얼(교재 누끼) 업로드, OT 영상, 유의사항 섹션, 실제 후기 교체 편집기
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
    "purpose_label": "",
    "purpose_type": "신규 커리큘럼", "target": "고3·N수",
    "custom_copy": None, "bg_photo_url": "",
    "active_sections": ["banner","intro","why","curriculum","cta"],
    "ai_mood": "", "inst_profile": None, "last_seed": None,
    "custom_section_on": False, "custom_section_topic": "",
    "uploaded_bg_b64": "",
    "pixabay_key": "", "bg_cache": {}, "preview_key": 0,
    "copy_tone": "담백·확신 (기본)",
    "page_angle": "자동 (AI가 선택)",
    "target_year": None,          # None이면 오늘 날짜로 자동 계산
    "allow_dday": False,          # D-day 숫자 표기 허용 (100일 이내 + 공식 일정일 때만 의미 있음)
    "fx_on": False,               # 파티클·글리치 등 배경 효과
    "kv_img_b64": "",             # 히어로 키비주얼(교재 표지·누끼 이미지)
    "notice_text": "",            # 유의사항
    "event_info": "",             # 이벤트 기간·발표일 등 (AI가 날짜를 지어내지 않도록)
    "_concept": None, "_last_ctx": "",
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
# ══════════════════════════════════════════════════════
# [v8] 카피 어조 · 기획 앵글 · 스타일 가이드
#  - 예전 COPY_TONES/FEW_SHOT_EXAMPLES를 통째로 교체한 블록입니다.
#  - 핵심: '하지 마라' 예시를 길게 나열하지 않고(모델이 오히려 따라 씀),
#          실제 대성마이맥 PR 페이지의 문법을 '이렇게 써라'로만 보여줍니다.
# ══════════════════════════════════════════════════════
GROQ_MODELS = [
    "openai/gpt-oss-120b",   # 메인 — 품질 좋음
    "openai/gpt-oss-20b",    # 보조 — 더 빠름
    "qwen/qwen3.8-27b",      # 백업
    "qwen/qwen3.6-27b",      # 구버전 백업 (없으면 자동으로 건너뜀)
]

COPY_TONES = {
    "담백·확신 (기본)": "존댓말. 짧고 단정한 문장. 과장 형용사 대신 학생이 겪는 장면과 이 강좌가 바꾸는 것을 담담하게 말한다. 확신은 단어가 아니라 구체성으로 보여준다.",
    "친근한 선배": "부드러운 존댓말(~해요). 학생이 실제로 하는 말을 그대로 옮겨 공감을 연다. 위로·응원 대신 '그럴 땐 이렇게' 식의 실용적인 다음 문장으로 잇는다.",
    "프리미엄·절제": "수식어를 최소화한 명사형·단문. 영문 eyebrow와 여백을 살리는 톤. 감탄문과 느낌표 금지.",
    "위트·트렌디": "말맛 있는 짧은 문장과 가벼운 반전. 유행어·밈은 페이지 전체에서 1개 이하. 과목 내용의 정확성은 그대로 유지.",
}

PAGE_ANGLES = {
    "자동 (AI가 선택)": "",
    "문제 → 해결": "THE PROBLEM(학생이 막히는 지점 진단) → THE SOLUTION(이 강좌의 원리) → 커리큘럼 → 수강 대상 순서로 설득한다.",
    "컨셉 메타포": "강좌명에서 비유 하나를 뽑아 히어로부터 CTA까지 그 이미지로 이야기를 끌고 간다. (예: 계단, 달의 위상, 응축과 폭발)",
    "시즌 선언": "지금 시기(아래 [시기 정보])에 학생이 해야 할 일을 선언하고, 그 일을 이 강좌가 맡는다는 구조로 쓴다.",
    "Old vs New": "학생이 지금 쓰는 방식(Old)과 이 강좌의 방식(New)을 대비시킨다. 대비 축은 하나만 쓴다.",
}

STYLE_GUIDE = """
[실제 대성마이맥 PR 페이지의 문법 — 이 문법을 따른다. 예시 문장을 그대로 베끼지는 말 것]

1) 히어로는 3단 구조: '킥커 한 줄' → 강좌명 워드마크 → '설명 1~2줄'
   - 킥커: 이 강좌가 무엇인지 비유로 정의한다.
       "1년을 담은 마지막 한 방울의 엑기스" / "감독해의 불안을 확신으로 바꾸는"
   - 워드마크: 강좌명을 그대로. 동사를 붙여 문장으로 만들지 않는다.
   - 설명: 무엇을, 누구에게, 어떻게. 숫자는 입력 정보에 있을 때만.
       "노베이스를 위한 100문장, 10일 완성" / "수능 영어의 본질은 번역이 아니라 [[논리]]입니다."

2) 섹션 헤드라인은 학생이 실제로 하는 말이나 겪는 장면이다. 질문 또는 단정, 한두 줄.
       "단어도 알고 해석도 되는데 왜 풀어내지를 못할까?"
       "시험장에서 눈앞이 [[흐려지는]] 경험"
       "열심히 하는데 제자리걸음인 것 같나요?"
   서브카피는 그 장면의 원인을 짚는 진단 한 문장.
       "단어는 아는데 문장이 튕겨 나간다면, 지금 '번역'을 하고 있는 것입니다."

3) 강조: 헤드라인 하나에 핵심어 딱 하나만 [[ ]]로 감싼다. (렌더러가 포인트 컬러로 칠함)

4) 영문 eyebrow: THE PROBLEM / THE SOLUTION / ROADMAP / PHILOSOPHY / OFFICIAL TRAILER 처럼
   2~3단어 영문 대문자. 문장형 영어 금지.

5) 컨셉 메타포는 하나만 정하고 히어로~CTA까지 일관되게 쓴다.
   (KEY STEP=계단, 매달 KISS=달의 위상, KISS LOGIC=오컴의 면도날, KISSENCE=응축과 폭발)

6) 말투: 존댓말이 기본. 한 문장에 한 가지 정보. 형용사보다 동사와 장면.
   카드 설명은 '학생 상황 한 문장 + 이 강좌가 바꾸는 것 한 문장'.

7) 쓰지 않는 표현: '체계적인', '최고의', '함께라면', '~의 비밀', '비법 공개', '여정', '첫걸음',
   '잠재력', '한계를 넘어', '~하는 당신', '지금 바로 시작하세요'(단독).
   확인되지 않은 숫자(합격자 수, 만족도 %, 'n등급→1등급', 'n주 만에') 금지.
"""

# ══════════════════════════════════════════════════════
# [v8] 수능 일정 · 시즌 계산 — 'D-100 남발'의 근본 해결
#  - 날짜는 AI가 지어내지 않고 파이썬이 계산합니다.
#  - D-day 숫자는 (1) 공식 일정이 확정돼 있고 (2) 100일 이내이고
#    (3) 사이드바에서 'D-day 표기 허용'을 켰을 때만 프롬프트에 들어갑니다.
#  - 일정이 새로 발표되면 아래 표에 한 줄만 추가하세요.
# ══════════════════════════════════════════════════════
import datetime as _dt
KST = _dt.timezone(_dt.timedelta(hours=9))

SUNEUNG_SCHEDULE = {   # key = 학년도
    2027: {"exam": _dt.date(2026, 11, 19), "mock6": _dt.date(2026, 6, 4), "mock9": _dt.date(2026, 9, 2)},
    2028: {"exam": _dt.date(2027, 11, 18), "mock6": None, "mock9": None},
}

def kst_today() -> _dt.date:
    return _dt.datetime.now(KST).date()

def exam_date_for(year: int):
    """학년도 → (수능일, 추정여부). 표에 없으면 11월 셋째 목요일로 추정."""
    if year in SUNEUNG_SCHEDULE:
        return SUNEUNG_SCHEDULE[year]["exam"], False
    d = _dt.date(year - 1, 11, 1)
    first_thu = d + _dt.timedelta(days=(3 - d.weekday()) % 7)
    return first_thu + _dt.timedelta(days=14), True

def default_target_year(today=None) -> int:
    """오늘 기준 '지금 만드는 페이지'가 겨냥할 학년도.
    수능 2주 전부터는 다음 학년도 신규 시즌 페이지를 만든다고 보고 다음 해로 넘깁니다."""
    today = today or kst_today()
    y = today.year + 1
    for _ in range(3):
        exam, _est = exam_date_for(y)
        if (exam - today).days > 14:
            return y
        y += 1
    return y

def get_season(year=None, today=None) -> dict:
    today = today or kst_today()
    year = year or st.session_state.get("target_year") or default_target_year(today)
    exam, estimated = exam_date_for(year)
    days = (exam - today).days
    if days > 300:
        label, guide = "신규 시즌 오픈기", (f"직전 수능이 막 끝났고 {year}학년도 커리큘럼을 처음 공개하는 시기. "
                       "'새 기준', '1년의 설계', '첫 단추'처럼 시작과 설계를 말한다. 수능 임박·마지막 기회 같은 말은 맞지 않다.")
    elif days > 240:
        label, guide = "겨울방학·개념 완성기", "방학 동안 기초와 개념의 틀을 잡는 시기. 3월 학평 전에 공부 방식을 세팅한다."
    elif days > 170:
        label, guide = "1학기·6월 모평 준비기", "3월 학평으로 위치를 확인했고, 6월 모평을 향해 방향을 점검하는 시기."
    elif days > 140:
        label, guide = "6월 모평 전후", "평가원 첫 실전. 결과를 점검하고 하반기 전략을 세우는 시기."
    elif days > 80:
        label, guide = "여름방학·실전 전환기", "개념에서 실전으로 넘어가는 시기. 약점 보완과 기출 심화."
    elif days > 60:
        label, guide = "9월 모평 전후", "마지막 평가원 모의고사. 파이널 진입 직전."
    elif days > 0:
        label, guide = "파이널", "새로운 것을 더하기보다 압축·정리하는 시기."
    else:
        label, guide = "수능 이후", "수능이 끝난 시기."
    dday_possible = (not estimated) and 0 < days <= 100
    dday_on = dday_possible and bool(st.session_state.get("allow_dday", False))
    return {"year": year, "exam": exam, "estimated": estimated, "days": days,
            "label": label, "guide": guide, "today": today,
            "dday_possible": dday_possible, "dday_on": dday_on,
            "dday_str": f"D-{days}" if dday_on else ""}

def season_prompt_block() -> str:
    s = get_season()
    exam_txt = f"{s['exam'].year}년 {s['exam'].month}월 {s['exam'].day}일" + (" (추정)" if s["estimated"] else "")
    lines = [
        "[시기 정보 — 파이썬이 계산한 사실. 이 블록 밖의 날짜·기간 숫자는 만들지 말 것]",
        f"- 오늘: {s['today'].isoformat()}",
        f"- 대상: {s['year']}학년도 수능 ({exam_txt}). 교재·강좌 연도 표기는 '{s['year']}'.",
        f"- 지금 시즌: {s['label']} — {s['guide']}",
    ]
    if s["dday_on"]:
        lines.append(f"- D-day 표기 허용: 쓸 경우 반드시 '{s['dday_str']}'만 사용. 다른 남은 일수 숫자 금지.")
    else:
        lines.append("- 남은 일수(D-숫자, 'n일 남았다', 'n주 남았다')는 쓰지 않는다. 시기는 시즌 이름이나 시험 이름으로만 말한다.")
    return "\n".join(lines)

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

# [v8] 기본 섹션 구성을 실제 PR 페이지 흐름(문제 제기 → 정체 → OT → 커리큘럼 → 대상 → 후기 → 교재 → FAQ → 신청 → 유의사항)으로 정리
PURPOSE_SECTIONS = {
    "신규 커리큘럼": ["banner","why","intro","video","curriculum","target","reviews","textbook_sale","faq","cta","notice"],
    "이벤트":       ["banner","event_overview","event_benefits","event_deadline","reviews","cta","notice"],
    "기획전":       ["fest_hero","fest_lineup","fest_benefits","fest_cta","notice"],
}
PURPOSE_HINTS = {
    "신규 커리큘럼": "📚 문제 제기 → 강좌의 정체 → 커리큘럼 → 신청 흐름",
    "이벤트":       "🎉 혜택·일정·참여 방법을 한눈에. 날짜는 사이드바에 직접 입력",
    "기획전":       "🏆 강사 라인업·통합 혜택 중심",
}
PURPOSE_THEME_HINTS = {
    "이벤트":       "목적이 이벤트(기간한정·혜택)입니다. 혜택이 잘 보이는 선명한 테마를 선택하세요.",
    "기획전":       "목적이 기획전(통합 라인업)입니다. 여러 강사가 함께 보여도 정돈돼 보이는 테마를 선택하세요.",
    "신규 커리큘럼":"목적이 신규 커리큘럼(강사 신뢰·전문성)입니다. 무게감 있는 테마를 선택하세요.",
}
SEC_LABELS = {
    "banner":"🏠 메인 배너","intro":"📖 강좌의 정체(솔루션)","why":"💡 문제 제기",
    "curriculum":"📚 커리큘럼","target":"🎯 수강 대상","reviews":"⭐ 수강평",
    "faq":"❓ FAQ","cta":"📣 수강신청","notice":"📄 유의사항",
    "video":"🎬 OT 영상",
    # [v11] '수강 전/후·학습법 시각화·구성 안내·학습 변화'는 내용이 겹치고 지어낸 문구(1~2주차, 수능 당일 등)가 많아 목록에서 뺐습니다.
    "event_overview":"📅 이벤트 개요","event_benefits":"🎁 이벤트 혜택",
    "event_deadline":"⏰ 마감 안내",
    "fest_hero":"🏆 기획전 히어로","fest_lineup":"👥 강사 라인업",
    "fest_benefits":"🎁 기획전 혜택","fest_cta":"📣 기획전 CTA",
    "custom_section":"✏️ 기타 섹션",
    "course_intro": "📖 강좌 소개(입력 기반)",
    "textbook_sale": "📦 교재 소개·판매",
    "instructor_philosophy": "💭 강사 철학",
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
import re

def _tail_batchim(word: str) -> str:
    """단어 끝소리 → 'none' | 'rieul' | 'other'. 영문·숫자는 발음 기준 추정 (LOGIC→ㄱ, KISS→없음, STEP→ㅂ)"""
    w = (word or "").strip()
    if not w:
        return "none"
    c = w[-1]
    if "가" <= c <= "힣":
        jong = (ord(c) - ord("가")) % 28
        return "none" if jong == 0 else "rieul" if jong == 8 else "other"
    if c.isdigit():
        return {"0": "other", "1": "rieul", "3": "other", "6": "other", "7": "rieul", "8": "rieul"}.get(c, "none")
    lw = w.lower()
    if lw.endswith(("ck", "ng", "mb")) or lw[-1] in "bcdgkmnpqtx":
        return "other"
    if lw[-1] == "l":
        return "rieul"
    return "none"

def fix_korean_particles(text: str, word: str = "") -> str:
    """[v11] 조사 보정은 '특정 단어(강좌명) 바로 뒤'에만 적용.
    예전 버전은 모든 단어 뒤의 '는/을/와'를 바꿔서 '읽는→읽은', '카드들을→카드들를', '효과→효와' 같은 오류를 만들었습니다."""
    if not text or not word or word not in text:
        return text
    tail = _tail_batchim(word)
    pairs = [("으로", "로"), ("을", "를"), ("은", "는"), ("과", "와"), ("이", "가"), ("이라", "라")]
    esc = re.escape(word)
    for with_b, without_b in pairs:
        if with_b == "으로":
            target = "로" if tail in ("none", "rieul") else "으로"
        else:
            target = without_b if tail == "none" else with_b
        text = re.sub(esc + r"(?:" + re.escape(with_b) + "|" + re.escape(without_b) + r")(?=[\s,\.·!\?\"\'()\-]|$)",
                      word + target, text)
    return text

def remove_series_suffix(text: str, plabel: str) -> str:
    if not plabel or not text:
        return text
    escaped = re.escape(plabel)
    text = re.sub(escaped + r'\s*시리즈', plabel, text)
    return text

# fix_korean_particles 함수의 rules 리스트에서
# 받침 없는 경우 처리가 잘못된 것 → postprocess_copy 후처리에 아래 추가

def _has_batchim_char(char: str) -> bool:
    if not char or not ('가' <= char <= '힣'): return False
    return (ord(char) - ord('가')) % 28 != 0

def postprocess_copy(text: str, plabel: str) -> str:
    text = remove_series_suffix(text, plabel)
    text = fix_korean_particles(text, plabel)   # [v11] 강좌명 바로 뒤 조사만 보정
    return text

def strip_hanja(text: str) -> str:
    """한자·일본어·인도네시아어 제거 + 조사 보정 통합 버전"""
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    import re

    # 1) 조사 보정 (받침 없으면 "로", 있으면 "으로")
    def _fix_euro(m):
        word = m.group(1)
        last = word[-1] if word else ''
        if not ('가' <= last <= '힣'):
            return m.group(0)   # [v11] 영문·숫자 뒤(LOGIC으로 등)는 건드리지 않음
        code = ord(last) - ord('가')
        jongseong = code % 28
        return word + '로' if jongseong == 0 or jongseong == 8 else word + '으로'
    text = re.sub(r'([가-힣a-zA-Z0-9]+)(?:으로|로)(?=[\s,\.·!\?]|$)', _fix_euro, text)

    # 2) 한자·특수문자 제거 (한글, 영문, 숫자, 기본 구두점만 허용)
    # [v8] 마스킹(김*우)·시간(07:00)·대시(—)·따옴표(‘’“”)·별점(★)·원(○)이 지워지던 문제 → 허용 문자 확대
    allowed_pattern = r'[^\u3131-\u3163\uAC00-\uD7A3a-zA-Z0-9\s\.\,\!\?\'\"\%\[\]\(\)\-\<\>~·/&+\n:;\*—–‘’“”★○→#@=_|※「」『』]'
    text = re.sub(allowed_pattern, '', text)

    # 3) 인도네시아어/말레이어 금지 단어 제거
    FORBIDDEN_WORDS = [
        r'\bmasih\b', r'\bdan\b', r'\bdengan\b', r'\buntuk\b',
        r'\bjuga\b', r'\batau\b', r'\btidak\b', r'\byang\b',
        r'\bini\b', r'\bitu\b', r'\bsaya\b', r'\bkamu\b',
        r'\bada\b', r'\bbisa\b', r'\bharus\b', r'\bsudah\b',
        r'\bakan\b', r'\bagar\b', r'\bpada\b', r'\bdari\b',
    ]
    for pattern in FORBIDDEN_WORDS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # 4) 연속 공백 정리
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

_DDAY_RE = re.compile(
    r'(D[\-–—]?\s?\d{1,4}(?:일)?)'
    r'|(남은\s?\d{1,4}\s?(?:일|주|개월))'
    r'|(\d{1,4}\s?(?:일|주|개월)\s?(?:전|후|남[가-힣]*|앞[가-힣]*))',
    re.IGNORECASE
)

def strip_dday_claims(text: str) -> str:
    """근거 없는 D-day/카운트다운 숫자를 문장에서 통째로 제거"""
    if not isinstance(text, str) or not text:
        return text
    if not _DDAY_RE.search(text):
        return text
    text = _DDAY_RE.sub("", text)
    text = re.sub(r'\s*,\s*,', ',', text)
    text = re.sub(r'(^|[\s(])[,·]\s*', r'\1', text)
    text = re.sub(r'\s*,\s*$', '', text)
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text
    
def clean_obj(obj):
    if isinstance(obj, str): return strip_hanja(obj)   # [v8] 날짜 표현은 polish_copy()가 문장 단위로 처리
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

def ensure_course_name_in_title(result: dict, plabel: str) -> dict:
    """
    AI가 강좌명을 임의로 합성·변형해 새 단어를 만드는 것을 방지.
    (예: "KISS Logic" → "KISSENCE" 처럼 원본에 없는 단어를 지어내는 경우)
    bannerTitle에 강좌명이 원문 그대로 없으면 강좌명으로 교정한다.
    """
    if not plabel or not isinstance(result, dict):
        return result
    plabel_norm = plabel.replace(" ", "").lower()
    if not plabel_norm:
        return result

    bt = str(result.get("bannerTitle", ""))
    if plabel_norm not in bt.replace(" ", "").lower():
        result["bannerTitle"] = plabel

    if "festHeroTitle" in result:
        fh = str(result.get("festHeroTitle", ""))
        if plabel_norm not in fh.replace(" ", "").lower():
            result["festHeroTitle"] = plabel

    return result
    
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

    cleaned = _clean(result)
    # 조사 교정 + 시리즈 제거를 재귀 적용
    def _postproc(obj):
        if isinstance(obj, str):
            return postprocess_copy(obj, plabel)
        if isinstance(obj, dict):
            return {k: _postproc(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_postproc(i) for i in obj]
        return obj
    return _postproc(cleaned)
    
def safe_json(raw: str) -> dict:
    import json, re
    
    raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
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
    
    def _try(x):
        try: return clean_obj(json.loads(x))
        except Exception: return None

    r = _try(s)
    if r: return r
    r = _try(s.replace("\n", " ").replace("\r", ""))
    if r: return r
    fixed = re.sub(r",\s*}", "}", s)
    fixed = re.sub(r",\s*]", "]", fixed)
    r = _try(fixed)
    if r: return r
    raise ValueError(
        f"AI 응답 파싱 실패 — 다시 시도해주세요\n"
        f"원인: JSON 형식 오류 (AI 모델이 올바른 형식으로 응답하지 않음)\n"
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
#  [v8] 버그 수정: gpt-oss 모델은 reasoning_effort="none"을 받지 않아 매번 400 에러가 나고
#       조용히 백업 모델로 넘어가고 있었습니다. 모델별로 올바른 파라미터를 보냅니다.
# ══════════════════════════════════════════════════════
GROQ_FREE_TPM = 8000   # 무료 요금제: 모델마다 분당 8,000토큰 (입력 + 요청한 최대 출력 합계로 계산됨)

def _groq_free() -> bool:
    return not str(st.session_state.get("groq_tier", "")).startswith("Developer")

def _est_tokens(text: str) -> int:
    """대략적인 토큰 수 (한글 ≈ 1.3자/토큰, 그 외 ≈ 3.5자/토큰) — 넉넉하게 10% 더"""
    ko = len(re.findall(r"[가-힣]", text))
    return int((ko / 1.3 + (len(text) - ko) / 3.5) * 1.1) + 60

def _model_params(model: str) -> dict:
    if model.startswith("openai/gpt-oss"):
        # 무료 요금제에선 생각(추론) 토큰이 출력 한도를 잡아먹으므로 low
        return {"reasoning_effort": "low" if _groq_free() else "medium", "include_reasoning": False}
    if model.startswith("qwen/"):
        return {"reasoning_effort": "none"}
    return {}

def call_ai(prompt: str, system: str = "", max_tokens: int = 2000, temperature: float = 0.8) -> str:
    """[v14] 무료 요금제 한도(분당 8천 토큰)에 맞춰 출력 길이를 자동 조절하고,
    한도에 걸리면 다른 모델로 넘어갔다가 필요하면 잠시 기다려 다시 시도합니다."""
    key = st.session_state.api_key.strip()
    if not key:
        raise ValueError("API 키가 없습니다. 사이드바에서 gsk_... 키를 입력해주세요.")
    sys_parts = [system] if system else []
    sys_parts.append(
        "Return ONLY one valid JSON object. No markdown fences, no commentary. "
        "Write all copy in natural Korean as a senior Korean copywriter would. "
        "Never use Chinese characters, Japanese kana, or Indonesian/Malay words. "
        "English is allowed only for course names, eyebrow labels and the English tagline."
    )
    messages = [{"role": "system", "content": "\n\n".join(sys_parts)},
                {"role": "user", "content": prompt}]
    free = _groq_free()
    est_in = _est_tokens(messages[0]["content"] + prompt)
    errors, waits = [], []
    for rnd in range(2):                      # 1회차: 모델 순서대로 / 2회차: 한도 풀릴 때까지 기다린 뒤 다시
        if rnd == 1:
            if not waits:
                break
            time.sleep(min(max(waits), 45))
            waits = []
        for model in GROQ_MODELS:
            want = max_tokens + (1500 if model.startswith("openai/gpt-oss") else 0)
            if free:
                want = min(want, GROQ_FREE_TPM - est_in - 150)
                if want < 900:
                    errors.append(f"{model}: 입력이 길어 무료 한도(분당 8천 토큰) 안에 답할 공간이 부족"); continue
            body = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": int(want),
                    "response_format": {"type": "json_object"}, **_model_params(model)}
            for attempt in range(3):
                try:
                    resp = requests.post(GROQ_URL,
                                         headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                                         json=body, timeout=120)
                except Exception as e:
                    errors.append(f"{model}: 네트워크 오류 {e}"); break
                if resp.status_code == 401:
                    raise Exception("🔑 API 키 오류 — console.groq.com에서 확인해주세요.")
                try:
                    msg = resp.json().get("error", {}).get("message", "") if not resp.ok else ""
                except Exception:
                    msg = resp.text[:200]
                if resp.status_code == 429:
                    if "per day" in msg or "(TPD)" in msg or "(RPD)" in msg:
                        errors.append(f"{model}: 오늘 사용량 소진"); break
                    try:
                        waits.append(float(resp.headers.get("retry-after") or 20))
                    except Exception:
                        waits.append(20)
                    errors.append(f"{model}: 분당 한도 — 다른 모델로"); break
                if resp.status_code == 413 and attempt < 2:
                    # 요청이 분당 한도보다 큼 → 출력 길이를 줄여 다시
                    m = re.search(r"Limit (\d+), Requested (\d+)", msg)
                    if m:
                        over = int(m.group(2)) - int(m.group(1))
                        body["max_tokens"] = int(body["max_tokens"]) - over - 200
                        if body["max_tokens"] >= 900:
                            continue
                    errors.append(f"{model}: 요청이 한도보다 큼"); break
                if resp.status_code == 400 and "response_format" in body:
                    # JSON 모드나 파라미터를 지원하지 않는 모델 → 한 번 더 단순하게 시도
                    body.pop("response_format", None)
                    body.pop("include_reasoning", None)
                    continue
                if not resp.ok:
                    errors.append(f"{model}: HTTP {resp.status_code} {(msg or resp.text)[:150]}"); break
                try:
                    data = resp.json()
                    text = data["choices"][0]["message"]["content"]
                    finish = data["choices"][0].get("finish_reason")
                except Exception as e:
                    errors.append(f"{model}: 응답 파싱 실패 {e}"); break
                if text and text.strip():
                    if finish == "length" and not text.rstrip().endswith("}"):
                        errors.append(f"{model}: 답이 길이 한도에서 잘림"); break
                    st.session_state["_last_model"] = model
                    st.session_state["_last_model_errors"] = errors
                    return text
                errors.append(f"{model}: 빈 응답"); break
    hint = (" · 무료 요금제 한도일 가능성이 큽니다. 1분 뒤 다시 누르거나, Groq에 카드를 등록해 Developer 요금제로 바꾸면 해결됩니다."
            if free and any("한도" in e or "소진" in e for e in errors) else "")
    raise Exception("모든 모델 실패 — " + " / ".join(errors[-4:]) + hint)

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
    """[v8] 강사 정보 요약 — 예전 버전은 이력 문장 속 시리즈명을 강좌명으로 치환하다가
    '2028 2028 KISS LOGIC LOGIC' 같은 깨진 문장을 AI에게 넘기고 있었습니다."""
    ip     = st.session_state.get("inst_profile") or {}
    name   = st.session_state.get("instructor_name", "")
    subj   = st.session_state.get("subject", "")
    plabel = st.session_state.get("purpose_label", "")
    norm = lambda x: re.sub(r"[\s'’]", "", str(x)).lower()
    lines = [f"- 강사: {name} 선생님 ({subj})" if name else f"- 과목: {subj}"]
    if ip.get("found"):
        if ip.get("teachingStyle"):
            lines.append(f"- 수업 스타일(참고): {ip['teachingStyle']}")
        if ip.get("strength"):
            lines.append(f"- 강점 키워드(참고): {ip['strength']}")
        if ip.get("slogan"):
            lines.append(f"- 강사 슬로건(참고용, 문구에 그대로 쓰지 말 것): {ip['slogan']}")
        others = []
        for m in list(ip.get("signatureMethods") or []) + list(ip.get("curriculum_series") or []):
            if not m or m == "없음":
                continue
            if plabel and (norm(m) in norm(plabel) or norm(plabel) in norm(m)):
                continue
            if m not in others:
                others.append(m)
        if others:
            lines.append(f"- 같은 강사의 다른 시리즈(이번 페이지에서는 언급 금지): {', '.join(others)}")
    return "\n".join(lines)

# ═══════════════════════════════════════════════════════
# [v8] 문구 품질 검사(lint) + 1회 자동 고쳐쓰기
#  - 예전: 정규식으로 'D-100'만 잘라내서 "수능 , 마지막 기회" 같은 깨진 문장이 남음
#  - 지금: 위반 필드만 골라 AI에게 다시 쓰게 하고, 그래도 남으면 '문장 단위'로 제거
# ═══════════════════════════════════════════════════════
_DDAY_ANY_RE = re.compile(
    r'D\s?[-–—]\s?\d{1,3}(?!\d)'
    r'|\d{1,3}\s?(?:일|주)\s?(?:남|전|앞|뒤)'
    r'|남은\s?\d{1,3}\s?(?:일|주|개월)'
    r'|백\s?일|100\s?일', re.I)
_FAKE_NUM_RE = re.compile(
    r'\d\s?등급\s?(?:→|->|에서|➜)\s?\d\s?등급'
    r'|\d{1,3}(?:\.\d)?\s?%'
    r'|합격생\s?\d|만족도|\d+\s?만\s?명'
    r'|\d+\s?(?:주|일|개월)\s?만에')
CLICHE_WORDS = [
    "체계적", "최고의", "함께라면", "의 비밀", "비법", "극대화", "혁신", "여정", "첫걸음",
    "새로운 차원", "한계를 넘어", "잠재력", "꿈을 응원", "놀라운 변화", "성공의 열쇠",
    "하는 당신", "당신을 위한", "지금 바로 시작하세요", "압도적인 결과", "차원이 다른",
    "와 함께하면", "과 함께하면", "와 함께라면", "과 함께라면", "두렵지 않", "해답을 찾", "자신감을 얻", "한 걸음 나아",
    "잡아드립니다", "책임지겠습니다", "완벽하게 대비",
]
_SKIP_LINT_KEYS = {"bannerVisual", "introVisual", "whyVisual", "concept", "videoUrl",
                   "bg_photo_url", "custom_section_data", "course_copy", "textbook_copy",
                   "_alts", "_needs", "hidden"}

def _walk(obj, fn, path=""):
    """문자열 필드마다 fn(path, text) → 새 text"""
    if isinstance(obj, str):
        return fn(path, obj)
    if isinstance(obj, dict):
        return {k: (v if k in _SKIP_LINT_KEYS else _walk(v, fn, f"{path}.{k}" if path else k)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk(v, fn, f"{path}[{i}]") for i, v in enumerate(obj)]
    return obj

def normalize_highlight(text: str) -> str:
    """[[ ]] 강조는 문자열당 1개만 남기고, 짝이 안 맞는 괄호는 제거"""
    if "[[" not in text and "]]" not in text:
        return text
    seen = {"n": 0}
    def _keep_first(m):
        seen["n"] += 1
        return m.group(0) if seen["n"] == 1 else m.group(1)
    text = re.sub(r'\[\[(.+?)\]\]', _keep_first, text)
    if text.count("[[") != text.count("]]"):
        text = text.replace("[[", "").replace("]]", "")
    return text

def _user_facts() -> str:
    """MD가 직접 입력한 정보 — 여기 있는 숫자·날짜는 '확인된 사실'로 보고 통과"""
    keys = ("_last_ctx", "course_info", "textbook_info", "event_info", "purpose_label", "metaphor")
    return re.sub(r"\s", "", " ".join(str(st.session_state.get(k) or "") for k in keys))

def _allowed_hit(hit: str, season: dict, facts: str) -> bool:
    h = re.sub(r"\s", "", hit)
    return (season["dday_on"] and h == season["dday_str"]) or (h and h in facts)

def lint_copy(cp: dict) -> dict:
    """{최상위키: [문제 설명,...]} 반환"""
    season = get_season()
    facts = _user_facts()
    issues = {}
    def _chk(path, t):
        top = re.split(r'[.\[]', path)[0]
        for m in _DDAY_ANY_RE.finditer(t):
            if not _allowed_hit(m.group(0), season, facts):
                issues.setdefault(top, []).append(f"근거 없는 남은 일수 표현 '{m.group(0)}'")
        for m in _FAKE_NUM_RE.finditer(t):
            if not _allowed_hit(m.group(0), season, facts):
                issues.setdefault(top, []).append(f"확인되지 않은 수치 '{m.group(0)}'")
        for w in CLICHE_WORDS:
            if w in t:
                issues.setdefault(top, []).append(f"상투적 표현 '{w}'")
        return t
    _walk(cp, _chk)
    return {k: sorted(set(v)) for k, v in issues.items()}

def _drop_bad_sentences(text: str) -> str:
    season = get_season()
    facts = _user_facts()
    parts = re.split(r'(?<=[.!?。])\s+|\n', text)
    keep = []
    for p in parts:
        bad = any(not _allowed_hit(m.group(0), season, facts)
                  for m in list(_DDAY_ANY_RE.finditer(p)) + list(_FAKE_NUM_RE.finditer(p)))
        if not bad:
            keep.append(p)
    return " ".join(keep).strip() if keep else ""

def polish_copy(cp: dict, brief: str) -> dict:
    """lint → 위반 필드만 1회 재작성 → 남은 건 문장 단위 제거"""
    cp = _walk(cp, lambda p, t: normalize_highlight(t))
    issues = lint_copy(cp)
    if issues:
        targets = {k: cp[k] for k in issues if k in cp}
        problems = "\n".join(f"- {k}: {', '.join(v)}" for k, v in issues.items())
        prompt = (
            f"{brief}\n\n아래 JSON 필드에 문제가 있습니다. 같은 키·같은 구조로, 문제만 없앤 새 문구를 쓰세요.\n"
            f"뜻과 길이는 비슷하게, 숫자를 지우는 대신 구체적인 장면이나 행동으로 바꾸세요.\n\n"
            f"[문제]\n{problems}\n\n[현재 값]\n{json.dumps(targets, ensure_ascii=False)}\n\nJSON만 반환:"
        )
        try:
            fixed = safe_json(call_ai(prompt, max_tokens=2000, temperature=0.6))
            for k, v in fixed.items():
                if k in targets and type(v) == type(targets[k]):
                    cp[k] = v
        except Exception:
            pass
    # 최후 안전장치: 그래도 남은 날짜·수치 문장은 '문장째' 제거 (단어만 잘라 깨진 문장 만들지 않음)
    def _final(path, t):
        season, facts = get_season(), _user_facts()
        hits = list(_DDAY_ANY_RE.finditer(t)) + list(_FAKE_NUM_RE.finditer(t))
        if any(not _allowed_hit(m.group(0), season, facts) for m in hits):
            return _drop_bad_sentences(t)   # 전부 위반이면 빈 칸(→ 섹션 재생성 버튼으로 다시 쓰기)
        return t
    cp = _walk(cp, _final)
    cp = _walk(cp, lambda p, t: normalize_highlight(t))
    return cp

# ═══════════════════════════════════════════════════════
# [v11] 교정 패스 — 맞춤법·어법·어색한 표현만 고치는 마지막 단계
#  (예: '지문을 읽은 게 두려워졌습니다', '내용이 멍들어서', '첫 단추를 채우세요' 같은 오류)
# ═══════════════════════════════════════════════════════
PROOF_SKIP_KEYS = {"type", "variant", "nav", "pack", "pct", "no", "concept_en", "_reviews_sample", "videoUrl", "bg_photo_url",
                   "_alts", "_needs", "hidden", "layout"}

def proofread_copy(obj, label: str = ""):
    """문자열만 골라 교정 → 같은 구조로 되돌림. 실패하면 원본 그대로."""
    if not st.session_state.get("api_key"):
        return obj
    flat = {}
    def _collect(o, path):
        if isinstance(o, str):
            if re.search(r"[가-힣]", o) and len(o) >= 4:
                flat[path] = o
        elif isinstance(o, dict):
            for k, v in o.items():
                if k not in PROOF_SKIP_KEYS:
                    _collect(v, f"{path}/{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                _collect(v, f"{path}/{i}")
    _collect(obj, "")
    if not flat:
        return obj
    prompt = (
        "당신은 출판사 교정 편집자입니다. 아래 JSON 값(한국어 광고 문구)을 교정하세요.\n"
        "[고칠 것] 맞춤법·띄어쓰기, 잘못된 어미·조사(예: '읽은 두려움'→'읽는 두려움'), 뜻이 뒤집히거나 어색한 표현"
        "(예: '첫 단추를 채우다'→'첫 단추를 끼우다', '내용이 멍들다'→'내용이 흐려지다'), 번역투, 같은 말 반복, "
        "억지로 붙인 비유(예: '문장은 파도, 우리는 서퍼다' → 비유를 빼고 평이하게).\n"
        "[고치지 말 것] 의미, 사실, 숫자, 강좌명·영문, [[ ]]·「 」·** 표시, 문장 길이. 새 내용 추가 금지. 이미 자연스러우면 그대로 둡니다.\n"
        f"[강좌명] {label}\n\n"
        f"{json.dumps(flat, ensure_ascii=False)}\n\n"
        "같은 키를 가진 JSON 하나만 반환:"
    )
    try:
        fixed = safe_json(call_ai(prompt, max_tokens=max(1500, len(prompt)), temperature=0.2))
    except Exception:
        return obj
    def _apply(o, path):
        if isinstance(o, str):
            v = fixed.get(path)
            if isinstance(v, str) and v.strip() and 0.6 <= len(v) / max(len(o), 1) <= 1.5:
                return v
            return o
        if isinstance(o, dict):
            return {k: (v if k in PROOF_SKIP_KEYS else _apply(v, f"{path}/{k}")) for k, v in o.items()}
        if isinstance(o, list):
            return [_apply(v, f"{path}/{i}") for i, v in enumerate(o)]
        return o
    return _apply(obj, "")

# ═══════════════════════════════════════════════════════
# [v8] 공통 브리프 — 전체 생성·섹션 재생성이 같은 기준을 쓰도록
# ═══════════════════════════════════════════════════════
def build_copy_brief(ctx: str = "") -> str:
    plabel = st.session_state.get("purpose_label", "").strip()
    subj   = st.session_state.get("subject", "영어")
    tgt    = st.session_state.get("target", "")
    tone   = COPY_TONES.get(st.session_state.get("copy_tone"), list(COPY_TONES.values())[0])
    angle  = PAGE_ANGLES.get(st.session_state.get("page_angle", ""), "")
    metaphor = st.session_state.get("metaphor", "").strip()
    concept  = st.session_state.get("_concept") or {}
    course_info   = st.session_state.get("course_info", "").strip()
    textbook_info = st.session_state.get("textbook_info", "").strip()
    event_info    = st.session_state.get("event_info", "").strip()

    parts = [
        "당신은 대성마이맥 컨텐츠기획실의 시니어 카피라이터입니다. 실제 강사 PR 페이지(상세페이지)에 바로 들어갈 문구를 씁니다.",
        STYLE_GUIDE,
        season_prompt_block(),
        "[강좌 정보 — 이 안에 없는 사실(경력, 수치, 교재 구성, 기간, 가격)은 지어내지 말 것]",
        f"- 강좌명(워드마크): {plabel or '(미입력)'}",
        f"- 과목: {subj} / 수강 대상: {tgt}",
        _get_instructor_context(),
    ]
    if course_info:   parts.append(f"- 강좌 상세(MD 입력): {course_info}")
    if textbook_info: parts.append(f"- 교재 정보(MD 입력): {textbook_info}")
    if event_info:    parts.append(f"- 이벤트 일정·조건(MD 입력, 이 값만 사용): {event_info}")
    if ctx:           parts.append(f"- 페이지 기획 메모(MD 입력, 최우선): {ctx}")
    if metaphor:
        parts.append(f"- 컨셉 메타포(지정): {metaphor} — 이 비유 하나로 페이지 전체를 끌고 갈 것. 단어 반복보다 이미지로.")
    elif concept.get("metaphor"):
        parts.append(f"- 이 페이지의 메타포(앞서 정함): {concept.get('metaphor')} / 키워드: {concept.get('keyword','')}")
    parts.append(f"[어조] {tone}")
    if angle:
        parts.append(f"[기획 앵글] {angle}")
    parts.append("[강좌명 규칙] 강좌명은 원문 그대로. 변형·합성 신조어 금지. 한 문장에 강좌명을 두 번 넣지 말 것.")
    return "\n".join(parts)

COPY_SCHEMAS = {
    "신규 커리큘럼": """{
 "concept": {"metaphor": "강좌명에서 뽑은 비유 하나 (예: 계단, 응축)", "keyword": "페이지를 관통하는 단어 하나"},
 "bannerSub": "히어로 상단 작은 라벨. 학년도·과목·대상 (예: 2028 수능 영어 · 고3·N수)",
 "bannerKicker": "워드마크 바로 위 한 줄. 강좌를 비유로 정의 (14~26자)",
 "bannerTitle": "강좌명 그대로",
 "bannerLead": "워드마크 아래 설명 1~2문장. 핵심어 하나만 [[ ]] (30~60자)",
 "brandTagline": "영문 슬로건 한 문장 (4~8단어)",
 "bannerTags": ["핵심 키워드", "핵심 키워드", "핵심 키워드"],
 "ctaCopy": "버튼 문구 (예: 수강신청 하기)",
 "whyEyebrow": "영문 2~3단어 (예: THE PROBLEM)",
 "whyTitle": "학생이 실제로 겪는 장면을 질문이나 단정으로. 핵심어 하나 [[ ]]. 30자 이내",
 "whySub": "그 장면의 원인을 짚는 진단 한 문장 (25~50자)",
 "whyReasons": [["01", "증상 이름 4~10자", "학생 목소리 같은 상황 한 문장 + 이 강좌가 바꾸는 것 한 문장 (50~90자)"], ["02", "", ""], ["03", "", ""]],
 "introEyebrow": "영문 2~3단어 (예: THE SOLUTION)",
 "introTitle": "강좌의 정체를 밝히는 선언. 예: '이게 바로, [[강좌명]]입니다.' (25자 이내)",
 "introDesc": "이 강좌가 무엇을 어떻게 다루는지. 입력된 정보 안에서 구체적으로 (80~150자)",
 "introBio": "강사 또는 강좌의 한 줄 포지션 (20~40자)",
 "videoTitle": "OT 영상 섹션 제목 (20자 이내, 핵심어 [[ ]])",
 "videoSub": "영상에서 확인할 수 있는 것 한 문장 (20~40자)",
 "curriculumEyebrow": "영문 (예: ROADMAP)",
 "curriculumTitle": "커리큘럼 섹션 제목 (25자 이내, 핵심어 [[ ]])",
 "curriculumSub": "단계를 밟으면 무엇이 달라지는지 한 문장 (20~45자)",
 "curriculumSteps": [["01", "단계명 2~8자", "이 단계에서 하는 것 + 끝나면 달라지는 것 (40~70자)", "기간 — 입력 정보에 없으면 빈 문자열"], ["02", "", "", ""], ["03", "", "", ""], ["04", "", "", ""]],
 "targetTitle": "수강 대상 섹션 제목 (20자 이내)",
 "targetItems": ["학생이 '내 얘기다' 할 구체 상황 (25~45자)", "", "", ""],
 "reviews": [["예시 후기 — 수치·과장 없이 공부 방식이 어떻게 바뀌었는지 (40~80자)", "김*우", "고3"], ["", "", ""], ["", "", ""]],
 "faqs": [["학생이 실제로 물어볼 질문", "입력 정보 기반 답변. 모르는 내용은 [확인 필요]"], ["", ""], ["", ""], ["", ""]],
 "ctaTitle": "마무리 제목 (25자 이내, 핵심어 [[ ]])",
 "ctaSub": "신청을 미루지 않을 이유 한 문장 — 시기 정보 안에서 (25~50자)",
 "ctaBadge": "짧은 라벨 (예: 2028 신규 개강)",
 "bannerVisual": "디자이너용 키비주얼 디렉션: 메타포를 어떤 오브젝트·색·구도로 보여줄지 (60~120자)",
 "introVisual": "디자이너용 디렉션 (40~80자)",
 "whyVisual": "디자이너용 디렉션 (40~80자)"
}""",
    "이벤트": """{
 "concept": {"metaphor": "이벤트 컨셉 비유 하나", "keyword": "키워드 하나"},
 "bannerSub": "상단 라벨 (예: 2028 KISS 수강생 EVENT)",
 "bannerKicker": "이벤트를 한 줄로 정의 (14~26자)",
 "bannerTitle": "이벤트명 또는 강좌명 (15자 이내)",
 "bannerLead": "참여하면 무엇을 받는지 1~2문장, 핵심어 [[ ]] (30~60자)",
 "brandTagline": "영문 한 문장", "bannerTags": ["", "", ""], "ctaCopy": "버튼 문구",
 "eventTitle": "이벤트 개요 제목 (20자 이내)", "eventDesc": "참여 방법 요약 (40~80자)",
 "eventDetails": [["📅", "이벤트 기간", "MD 입력값, 없으면 [기간 입력]"], ["🎯", "참여 대상", "값"], ["🎁", "혜택", "값"]],
 "benefitsTitle": "혜택 섹션 제목 (20자 이내)",
 "eventBenefits": [{"no": "01", "icon": "이모지 1개", "title": "혜택명", "desc": "40~70자", "badge": "8자 이내"}, {"no": "02", "icon": "", "title": "", "desc": "", "badge": ""}, {"no": "03", "icon": "", "title": "", "desc": "", "badge": ""}],
 "deadlineTitle": "마감 안내 제목 (20자 이내)", "deadlineMsg": "마감 조건 안내 (40~80자, 날짜는 MD 입력값만)",
 "reviews": [["예시 후기 40~80자", "김*우", "고3"], ["", "", ""], ["", "", ""]],
 "ctaTitle": "마무리 제목 (핵심어 [[ ]])", "ctaSub": "25~50자", "ctaBadge": "짧은 라벨"
}""",
    "기획전": """{
 "concept": {"metaphor": "기획전 컨셉 비유 하나", "keyword": "키워드 하나"},
 "festHeroTitle": "기획전명 (15자 이내)", "festHeroCopy": "한 줄 정의 (14~26자)",
 "festHeroSub": "무엇을 한 번에 얻는지 (40~70자)", "brandTagline": "영문 한 문장",
 "festHeroStats": [], "festLineupTitle": "라인업 제목 (20자 이내)", "festLineupSub": "30~50자",
 "festLineup": [{"name": "강사명(입력값만, 없으면 [강사명])", "tag": "분야", "tagline": "30~50자", "badge": "8자 이내", "emoji": ""}],
 "festBenefitsTitle": "혜택 제목", "festBenefits": [{"no": "01", "icon": "", "title": "혜택명", "desc": "40~70자", "badge": "8자 이내"}],
 "festCtaTitle": "마무리 제목 (핵심어 [[ ]])", "festCtaSub": "30~60자"
}""",
}

def gen_copy(ctx: str, ptype: str, tgt: str, plabel: str) -> dict:
    st.session_state["_concept"] = None          # 새 페이지마다 메타포 새로 정함
    brief = build_copy_brief(ctx)
    schema = COPY_SCHEMAS.get(ptype, COPY_SCHEMAS["신규 커리큘럼"])
    prompt = (
        f"{brief}\n\n"
        "[작성 순서] 먼저 concept(메타포·키워드)를 정하고, 그 메타포로 나머지 필드를 쓰세요. "
        "각 필드 설명의 글자 수를 지키고, 빈 칸 예시(\"\")도 같은 형식으로 채우세요.\n\n"
        f"JSON만 반환:\n{schema}"
    )
    result = safe_json(call_ai(prompt, max_tokens=4000))
    plabel = st.session_state.get("purpose_label", "").strip()
    result = clean_obj(result)
    result = ban_other_curricula(result, plabel)
    if ptype != "이벤트":
        result = ensure_course_name_in_title(result, plabel)
    if isinstance(result.get("concept"), dict):
        st.session_state["_concept"] = result["concept"]
    result = polish_copy(result, brief)
    result = proofread_copy(result, plabel)
    if result.get("reviews"):
        result["_reviews_sample"] = True   # AI 예시 후기 표시(실제 후기로 교체 전까지 미리보기에 안내 노출)
    return result

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

# [v8] 랜덤 '문구 스타일 룰렛'(사이비 교주형, 감성 새벽형 등)은 제거했습니다.
#      톤은 사이드바의 '카피 어조', 구조는 '기획 앵글'로 MD가 직접 고릅니다.
def get_copy_variation() -> str:
    return ""

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
# [v8] 섹션별 문구 재생성 — 전체 생성과 같은 브리프·같은 검사 사용
# ═══════════════════════════════════════════════════════
SECTION_SCHEMAS = {
    "banner": '{"bannerSub":"상단 라벨","bannerKicker":"한 줄 비유 정의 14~26자","bannerTitle":"강좌명 그대로","bannerLead":"설명 1~2문장, 핵심어 [[ ]] 30~60자","brandTagline":"영문 한 문장","bannerTags":["","",""],"ctaCopy":"버튼 문구","bannerVisual":"키비주얼 디렉션 60~120자"}',
    "intro": '{"introEyebrow":"영문 2~3단어","introTitle":"강좌의 정체 선언, 핵심어 [[ ]] 25자 이내","introDesc":"80~150자","introBio":"20~40자","introVisual":"40~80자"}',
    "why": '{"whyEyebrow":"영문 2~3단어","whyTitle":"학생이 겪는 장면, 핵심어 [[ ]] 30자 이내","whySub":"진단 한 문장 25~50자","whyReasons":[["01","증상 이름 4~10자","상황 한 문장 + 바뀌는 것 한 문장 50~90자"],["02","",""],["03","",""]],"whyVisual":"40~80자"}',
    "curriculum": '{"curriculumEyebrow":"영문","curriculumTitle":"25자 이내, 핵심어 [[ ]]","curriculumSub":"20~45자","curriculumSteps":[["01","단계명 2~8자","40~70자","기간(입력 정보에 없으면 빈 문자열)"],["02","","",""],["03","","",""],["04","","",""]]}',
    "target": '{"targetTitle":"20자 이내","targetItems":["구체 상황 25~45자","","",""]}',
    "reviews": '{"reviews":[["예시 후기 40~80자, 수치·과장 없이","김*우","고3"],["","",""],["","",""]]}',
    "faq": '{"faqs":[["실제 질문","입력 정보 기반 답, 모르면 [확인 필요]"],["",""],["",""],["",""]]}',
    "cta": '{"ctaTitle":"25자 이내, 핵심어 [[ ]]","ctaSub":"25~50자","ctaCopy":"버튼 문구","ctaBadge":"짧은 라벨"}',
    "video": '{"videoTitle":"20자 이내, 핵심어 [[ ]]","videoSub":"20~40자","videoTag":"OFFICIAL TRAILER"}',
    "event_overview": '{"eventTitle":"20자 이내","eventDesc":"40~80자","eventDetails":[["📅","이벤트 기간","MD 입력값, 없으면 [기간 입력]"],["🎯","참여 대상","값"],["🎁","혜택","값"]]}',
    "event_benefits": '{"benefitsTitle":"20자 이내","eventBenefits":[{"no":"01","icon":"이모지 1개","title":"혜택명","desc":"40~70자","badge":"8자 이내"},{"no":"02","icon":"","title":"","desc":"","badge":""},{"no":"03","icon":"","title":"","desc":"","badge":""}]}',
    "event_deadline": '{"deadlineTitle":"20자 이내","deadlineMsg":"40~80자, 날짜는 MD 입력값만","ctaCopy":"버튼 문구"}',
    "fest_hero": '{"festHeroTitle":"15자 이내","festHeroCopy":"14~26자","festHeroSub":"40~70자","brandTagline":"영문 한 문장","festHeroStats":[]}',
    "fest_lineup": '{"festLineupTitle":"20자 이내","festLineupSub":"30~50자","festLineup":[{"name":"강사명(입력값만, 없으면 [강사명])","tag":"분야","tagline":"30~50자","badge":"8자 이내","emoji":""}]}',
    "fest_benefits": '{"festBenefitsTitle":"20자 이내","festBenefits":[{"no":"01","icon":"","title":"혜택명","desc":"40~70자","badge":"8자 이내"},{"no":"02","icon":"","title":"","desc":"","badge":""},{"no":"03","icon":"","title":"","desc":"","badge":""}]}',
    "fest_cta": '{"festCtaTitle":"핵심어 [[ ]]","festCtaSub":"30~60자"}',
    "before_after": '{"baTitle":"25자 이내","baSub":"20~40자","baBeforeItems":["수강 전 구체 상황 25~45자","",""],"baAfterItems":["수강 후 달라지는 행동 25~45자","",""]}',
    "method": '{"methodTitle":"25자 이내","methodSub":"20~40자","methodSteps":[{"step":"STEP 01","label":"단계명","desc":"40~70자"},{"step":"STEP 02","label":"","desc":""},{"step":"STEP 03","label":"","desc":""}]}',
    "package": '{"pkgTitle":"25자 이내","pkgSub":"20~40자","packages":[{"icon":"📗","name":"구성명(입력 정보 기반)","desc":"30~60자","badge":"필수/포함/특전"}]}',
    "grade_stats": '{"gradeTitle":"25자 이내","gradeSub":"20~40자"}',
}

def gen_section(sec_id: str) -> dict:
    brief = build_copy_brief(st.session_state.get("_last_ctx", ""))
    schema = SECTION_SCHEMAS.get(sec_id, '{"title":"제목","desc":"설명"}')
    sec_name = SEC_LABELS.get(sec_id, sec_id)
    cur = st.session_state.get("custom_copy") or {}
    keep = {k: cur.get(k) for k in ("bannerTitle", "bannerKicker", "bannerLead", "whyTitle", "introTitle") if cur.get(k)}
    ctx_line = f"\n[이미 페이지에 있는 문구 — 톤을 맞추되 같은 표현을 반복하지 말 것]\n{json.dumps(keep, ensure_ascii=False)}" if keep else ""
    ptype = st.session_state.get("purpose_type", "신규 커리큘럼")
    extra = ""
    if sec_id == "banner" and ptype == "이벤트":
        extra = "\n[이벤트 배너] bannerTitle은 이벤트 성격이 드러나는 이름으로. 강좌명을 억지로 넣지 말 것."
    prompt = (f"{brief}{ctx_line}{extra}\n\n'{sec_name}' 섹션 문구만 새로 쓰세요. "
              f"이전 버전과 다른 각도로 쓰되 같은 메타포를 유지하세요.\n\nJSON만 반환:\n{schema}")
    last_err = None
    plabel = st.session_state.get("purpose_label", "").strip()
    for attempt in range(2):
        try:
            result = safe_json(call_ai(prompt, max_tokens=2000, temperature=0.9))
            result = ban_other_curricula(result, plabel)
            if sec_id == "banner" and ptype != "이벤트":
                result = ensure_course_name_in_title(result, plabel)
            result = polish_copy(result, brief)
            result = proofread_copy(result, plabel)
            if sec_id == "reviews":
                result["_reviews_sample"] = True
            return result
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
# [v8] 디자인 시스템 CSS — '판에 박힌 AI 템플릿' 느낌의 원인 정리
#  1) 한글 헤드라인이 Bebas/Orbitron 같은 영문 폰트로 지정돼 시스템 폰트로 깨져 보이던 문제
#     → 한글은 Pretendard로 통일(--fh), 테마 폰트는 워드마크·영문 라벨에만(--fd)
#  2) 섹션마다 64~80px 제목, 마키, 워터마크 숫자, 글리치가 겹쳐 보이던 문제
#     → 실제 PR 페이지처럼 eyebrow + 2줄 헤드라인 + 서브카피의 일정한 리듬
# ══════════════════════════════════════════════════════
DS_CSS = """
:root{--fk:'Pretendard Variable',Pretendard,-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR',sans-serif;--maxw:1080px}
body{font-family:var(--fk);font-size:16px;letter-spacing:-.01em;line-height:1.6}
.ds-sec{padding:clamp(72px,9vw,128px) clamp(20px,5vw,40px);position:relative;background:var(--bg);color:var(--text)}
.ds-sec.bg2{background:var(--bg2)}
.ds-sec.bg3{background:var(--bg3)}
.ds-in{max-width:var(--maxw);margin:0 auto;position:relative;z-index:1}
.ds-head{text-align:center;margin:0 auto clamp(40px,5vw,60px);max-width:760px}
.ds-head.left{text-align:left;margin-left:0}
.ds-eyebrow{display:inline-block;font-family:var(--fd),var(--fk);font-size:12px;font-weight:800;letter-spacing:.16em;
  text-transform:uppercase;color:var(--c1);padding:6px 14px;border:1.5px solid currentColor;border-radius:999px;margin-bottom:20px;line-height:1.2}
.ds-h2{font-family:var(--fk);font-size:clamp(26px,3.4vw,42px);font-weight:800;line-height:1.34;letter-spacing:-.035em;color:var(--text);word-break:keep-all;margin:0}
.ds-sub{margin:16px 0 0;font-size:clamp(15px,1.35vw,18px);line-height:1.75;color:var(--t70);word-break:keep-all}
.hl{color:var(--c1)}
.hl-box{background:var(--c1);color:var(--on-c1,#fff);padding:0 .2em;box-decoration-break:clone;-webkit-box-decoration-break:clone}
.ds-grid{display:grid;gap:16px}
.ds-g2{grid-template-columns:repeat(2,1fr)}
.ds-g3{grid-template-columns:repeat(3,1fr)}
.ds-g4{grid-template-columns:repeat(4,1fr)}
.ds-card{background:var(--bg);border:1px solid var(--bd);border-radius:var(--r,12px);padding:30px 28px;color:var(--text)}
.ds-sec.bg2 .ds-card,.ds-sec.bg3 .ds-card{background:var(--bg)}
.ds-card h3{font-family:var(--fk);font-size:19px;font-weight:800;letter-spacing:-.03em;line-height:1.4;margin:16px 0 10px;color:var(--text)}
.ds-card p{font-size:15px;line-height:1.75;color:var(--t70);margin:0;word-break:keep-all}
.ds-num{display:inline-flex;align-items:center;justify-content:center;min-width:36px;height:36px;padding:0 10px;border-radius:999px;
  background:var(--c1);color:var(--on-c1,#fff);font-family:var(--fd),var(--fk);font-weight:800;font-size:13px;letter-spacing:.04em}
.ds-chip{display:inline-block;font-size:12px;font-weight:700;padding:5px 12px;border-radius:999px;border:1px solid var(--bd);color:var(--t70);background:var(--bg)}
.ds-btns{display:flex;gap:10px;flex-wrap:wrap}
.ds-btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:56px;padding:0 30px;border-radius:var(--r-btn,8px);
  font-family:var(--fk);font-weight:800;font-size:16px;letter-spacing:-.01em;background:var(--c1);color:var(--on-c1,#fff);border:1.5px solid var(--c1);text-decoration:none;transition:transform .15s,opacity .15s}
.ds-btn:hover{transform:translateY(-1px);opacity:.92}
.ds-btn.ghost{background:transparent;color:var(--text);border-color:var(--bd)}
.ds-wordmark{font-family:var(--fd),var(--fk);font-weight:900;line-height:.98;letter-spacing:-.02em;color:var(--text);margin:0;word-break:keep-all}
.ds-kicker{font-size:clamp(16px,1.7vw,22px);font-weight:700;letter-spacing:-.02em;color:var(--text);margin:0 0 18px}
.ds-lead{font-size:clamp(16px,1.5vw,20px);line-height:1.7;color:var(--t70);margin:26px 0 0;word-break:keep-all}
.ds-badge{display:inline-block;font-size:13px;font-weight:700;letter-spacing:.02em;padding:7px 16px;border-radius:999px;
  background:color-mix(in srgb,var(--c1) 14%,transparent);color:var(--c1);margin-bottom:24px}
.ds-tagline{margin-top:36px;font-family:var(--fd),var(--fk);font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:var(--t45)}
.ds-split{display:grid;grid-template-columns:1fr 1fr;gap:clamp(32px,6vw,80px);align-items:center}
.ds-steps{counter-reset:s}
.ds-step{position:relative}
.ds-step-top{display:flex;justify-content:space-between;align-items:center;gap:8px}
.ds-step-no{font-family:var(--fd),var(--fk);font-size:13px;font-weight:800;letter-spacing:.12em;color:var(--c1)}
.ds-check{display:flex;gap:14px;align-items:flex-start}
.ds-check svg{flex-shrink:0;margin-top:2px}
.ds-check p{font-size:16px;font-weight:600;color:var(--text);line-height:1.6;margin:0}
.ds-quote p{font-size:15.5px;color:var(--text);line-height:1.8}
.ds-stars{color:var(--c1);letter-spacing:2px;font-size:14px}
.ds-meta{margin-top:18px;padding-top:16px;border-top:1px solid var(--bd);display:flex;justify-content:space-between;font-size:13px;color:var(--t45)}
.ds-sample{margin:24px auto 0;max-width:760px;text-align:center;font-size:12.5px;color:var(--t45);border:1px dashed var(--bd);padding:10px 14px;border-radius:8px}
.ds-faq{max-width:820px;margin:0 auto;border-top:2px solid var(--text)}
.ds-faq details{border-bottom:1px solid var(--bd)}
.ds-faq summary{list-style:none;cursor:pointer;padding:22px 4px;display:flex;gap:14px;align-items:flex-start;font-weight:700;font-size:16.5px;color:var(--text)}
.ds-faq summary::-webkit-details-marker{display:none}
.ds-faq summary b{color:var(--c1);font-family:var(--fd),var(--fk)}
.ds-faq summary::after{content:'+';margin-left:auto;color:var(--t45);font-weight:400;font-size:22px;line-height:1}
.ds-faq details[open] summary::after{content:'−'}
.ds-faq .a{padding:0 4px 24px 34px;color:var(--t70);font-size:15px;line-height:1.8}
.ds-note{margin:28px 0 0;padding:18px 22px;border-left:3px solid var(--c1);background:var(--bg2);font-weight:700;color:var(--text);line-height:1.7}
.ds-cta{padding:clamp(80px,10vw,128px) clamp(20px,5vw,40px);text-align:center}
.ds-notice{background:#111;color:rgba(255,255,255,.62);padding:56px clamp(20px,5vw,40px)}
.ds-notice h4{color:#fff;font-size:15px;font-weight:800;margin:0 0 16px}
.ds-notice ul{margin:0;padding-left:18px}
.ds-notice li{font-size:13px;line-height:1.9}
.ds-video{aspect-ratio:16/9;width:100%;border-radius:var(--r,12px);overflow:hidden;background:var(--bg3);border:1px solid var(--bd);display:flex;align-items:center;justify-content:center;color:var(--t45)}
.ds-video iframe{width:100%;height:100%;border:0}
.ds-kv img{width:100%;max-height:560px;object-fit:contain;filter:drop-shadow(0 30px 40px rgba(0,0,0,.25))}
@media(max-width:860px){
  .ds-g2,.ds-g3,.ds-g4,.ds-split{grid-template-columns:1fr!important}
  .ds-head.left{text-align:center}
}
/* 레거시 섹션(전후비교·교재 등)도 같은 타이포 리듬으로 맞춤 */
.sec h2,.sec .sec-h2{font-family:var(--fk)!important;font-size:clamp(26px,3.4vw,42px)!important;line-height:1.34!important;letter-spacing:-.035em!important;font-weight:800!important}
.sec h3,.sec h4{font-family:var(--fk)!important;letter-spacing:-.03em!important}
.sec{padding:clamp(72px,9vw,128px) clamp(20px,5vw,40px)!important}
.tag-line{font-family:var(--fd),var(--fk);font-size:12px!important;letter-spacing:.16em!important}
.marquee-container,.typo-watermark{display:none!important}
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
# ══════════════════════════════════════════════════════
# [v8] 섹션 렌더러 — 핵심 섹션 전면 교체
#  - 랜덤/해시로 레이아웃이 매번 바뀌던 구조 제거 → 같은 입력이면 같은 결과
#  - 이모지 아이콘·★ 남발·하드코딩 감성 문구 제거
#  - 문구는 [[핵심어]] 강조 → 포인트 컬러로 표시
# ══════════════════════════════════════════════════════
import html as _html

def _t(v) -> str:
    """AI/사용자 문구 → 안전한 HTML (줄바꿈 → <br>, [[ ]] → 강조)"""
    s = strip_hanja(str(v or ""))
    s = s.replace("<br>", "\n").replace("<br/>", "\n")
    s = _html.escape(s, quote=False)
    s = re.sub(r'\[\[(.+?)\]\]', r'<span class="hl">\1</span>', s)
    return s.replace("\n", "<br>")

def _head(eyebrow: str, title: str, sub: str = "", align: str = "center") -> str:
    cls = "ds-head" + ("" if align == "center" else " left")
    return (f'<div class="{cls} rv">'
            + (f'<div class="ds-eyebrow">{_t(eyebrow)}</div><br>' if eyebrow else "")
            + f'<h2 class="ds-h2">{_t(title)}</h2>'
            + (f'<p class="ds-sub">{_t(sub)}</p>' if sub else "")
            + '</div>')

def _check_svg() -> str:
    return ('<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">'
            '<circle cx="12" cy="12" r="12" fill="var(--c1)"/>'
            '<path d="M7 12.5l3.2 3.2L17 9" fill="none" stroke="var(--on-c1,#fff)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>')

def _bg_vars(bg_url, dark):   # (레거시 호환용 — 다른 코드에서 쓸 수 있어 유지)
    if not bg_url:
        return {"hero_bg": "background:var(--bg)", "overlay": "", "tc": "color:var(--text)",
                "t70c": "color:var(--t70)", "c1c": "var(--c1)", "bdc": "var(--bd)",
                "card_bg": "rgba(255,255,255,.05)" if dark else "var(--bg)",
                "btn_s": "", "top_brd": "var(--bd)", "blur": ""}
    return {"hero_bg": f"background:var(--bg) url('{bg_url}') center/cover no-repeat",
            "overlay": '<div style="position:absolute;inset:0;background:rgba(0,0,0,0.60);z-index:1;pointer-events:none"></div>',
            "tc": "color:#fff", "t70c": "color:rgba(255,255,255,.82)", "c1c": "#fff",
            "bdc": "rgba(255,255,255,.28)", "card_bg": "rgba(0,0,0,.7)",
            "btn_s": "color:#fff;border-color:rgba(255,255,255,.4)",
            "top_brd": "rgba(255,255,255,.22)", "blur": "backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);"}


def sec_banner(d, cp, T):
    title   = cp.get("bannerTitle") or d["purpose_label"] or f'{d["subject"]} 강좌'
    kicker  = cp.get("bannerKicker", "")
    lead    = cp.get("bannerLead", "")
    sub     = cp.get("bannerSub", "")
    tagline = cp.get("brandTagline", "")
    cta     = cp.get("ctaCopy") or "수강신청 하기"
    bg_url  = cp.get("bg_photo_url", "")
    kv      = st.session_state.get("kv_img_b64", "")
    active  = st.session_state.get("active_sections", [])
    second  = ('<a class="ds-btn ghost" href="#video">OT 영상 보기</a>' if "video" in active
               else '<a class="ds-btn ghost" href="#curriculum">커리큘럼 보기</a>' if "curriculum" in active else "")
    n = len(strip_hanja(title))
    size = "clamp(56px,10vw,136px)" if n <= 10 else "clamp(44px,7.5vw,104px)" if n <= 16 else "clamp(36px,5.5vw,76px)"

    # 배경 사진이 있으면 그 섹션 안에서만 글자색 변수를 흰색으로 덮어씀 → 가독성 자동 확보
    if bg_url:
        sec_style = (f"background:linear-gradient(180deg,rgba(0,0,0,.45),rgba(0,0,0,.72)),url('{bg_url}') center/cover no-repeat;"
                     "--text:#fff;--t70:rgba(255,255,255,.82);--t45:rgba(255,255,255,.6);--bd:rgba(255,255,255,.35);")
    else:
        sec_style = ("background:radial-gradient(70% 55% at 50% 0%,color-mix(in srgb,var(--c1) 16%,transparent),transparent 70%),var(--bg);")

    align_center = not kv
    text_html = (
        (f'<div class="ds-badge">{_t(sub)}</div>' if sub else "")
        + (f'<p class="ds-kicker">{_t(kicker)}</p>' if kicker else "")
        + f'<h1 class="ds-wordmark st" style="font-size:{size}">{_t(title)}</h1>'
        + (f'<p class="ds-lead">{_t(lead)}</p>' if lead else "")
        + f'<div class="ds-btns" style="margin-top:40px;{"justify-content:center" if align_center else ""}">'
        + f'<a class="ds-btn" href="#cta">{_t(cta)}</a>{second}</div>'
        + (f'<div class="ds-tagline">{_t(tagline)}</div>' if tagline else "")
    )
    if kv:
        inner = (f'<div class="ds-split"><div class="rv">{text_html}</div>'
                 f'<div class="ds-kv rv d1"><img src="{kv}" alt="{_html.escape(strip_hanja(title))}"></div></div>')
    else:
        inner = f'<div class="rv" style="text-align:center;max-width:880px;margin:0 auto">{text_html}</div>'
    return (f'<section id="hero" class="ds-sec" style="min-height:min(92vh,880px);display:flex;align-items:center;'
            f'padding-top:clamp(96px,12vw,150px);padding-bottom:clamp(80px,10vw,130px);{sec_style}">'
            f'<div class="ds-in" style="width:100%">{inner}</div></section>')


def sec_why(d, cp, T):
    reasons = []
    for it in cp.get("whyReasons", []) or []:
        if isinstance(it, (list, tuple)) and len(it) >= 3:
            reasons.append((str(it[0]), str(it[1]), str(it[2])))
        elif isinstance(it, dict):
            reasons.append((str(it.get("no", "")), str(it.get("title", "")), str(it.get("desc", ""))))
    if not reasons:
        return ""
    cards = "".join(
        f'<div class="ds-card rv d{min(i+1,4)}"><span class="ds-num">{i+1:02d}</span>'
        f'<h3>{_t(tt)}</h3><p>{_t(dc)}</p></div>'
        for i, (_no, tt, dc) in enumerate(reasons[:4]))
    g = "ds-g3" if len(reasons) == 3 else "ds-g2"
    return (f'<section id="why" class="ds-sec bg2"><div class="ds-in">'
            + _head(cp.get("whyEyebrow") or "THE PROBLEM", cp.get("whyTitle") or "이런 고민, 하고 있지 않나요?", cp.get("whySub", ""))
            + f'<div class="ds-grid {g}">{cards}</div></div></section>')


def sec_intro(d, cp, T):
    label = d["purpose_label"] or d["subject"]
    title = cp.get("introTitle") or f"이게 바로,\n[[{label}]]입니다."
    desc  = cp.get("introDesc", "")
    bio   = cp.get("introBio", "")
    if not desc and not cp.get("introTitle"):
        return ""
    chips = "".join(f'<span class="ds-chip">{_t(x)}</span>' for x in [d["subject"], d.get("target", "")] + list(cp.get("bannerTags") or [])[:3] if x)
    return (f'<section id="intro" class="ds-sec"><div class="ds-in"><div class="ds-split" style="align-items:start">'
            f'<div class="rv"><div class="ds-eyebrow">{_t(cp.get("introEyebrow") or "THE SOLUTION")}</div><br>'
            f'<h2 class="ds-h2" style="font-size:clamp(30px,4vw,52px)">{_t(title)}</h2></div>'
            f'<div class="rv d1"><p style="font-size:clamp(16px,1.4vw,18px);line-height:1.95;color:var(--t70);margin:0;word-break:keep-all">{_t(desc)}</p>'
            + (f'<p class="ds-note">{_t(bio)}</p>' if bio else "")
            + (f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:24px">{chips}</div>' if chips else "")
            + '</div></div></div></section>')


def sec_curriculum(d, cp, T):
    steps = [s for s in (cp.get("curriculumSteps") or []) if isinstance(s, (list, tuple)) and len(s) >= 3]
    if not steps:
        return ""
    n = len(steps)
    g = {1: "ds-g2", 2: "ds-g2", 3: "ds-g3"}.get(n, "ds-g4" if n == 4 else "ds-g3")
    cards = ""
    for i, s in enumerate(steps):
        period = str(s[3]).strip() if len(s) > 3 else ""
        cards += (f'<div class="ds-card ds-step rv d{min(i+1,4)}" style="border-top:3px solid var(--c1)">'
                  f'<div class="ds-step-top"><span class="ds-step-no">STEP {i+1:02d}</span>'
                  + (f'<span class="ds-chip">{_t(period)}</span>' if period else "")
                  + f'</div><h3>{_t(s[1])}</h3><p>{_t(s[2])}</p></div>')
    return (f'<section id="curriculum" class="ds-sec bg2"><div class="ds-in">'
            + _head(cp.get("curriculumEyebrow") or "ROADMAP", cp.get("curriculumTitle") or f"{d['purpose_label']} 커리큘럼", cp.get("curriculumSub", ""))
            + f'<div class="ds-grid {g} ds-steps">{cards}</div></div></section>')


def sec_target(d, cp, T):
    items = [x for x in (cp.get("targetItems") or []) if str(x).strip()]
    if not items:
        return ""
    cards = "".join(f'<div class="ds-card ds-check rv d{min(i+1,4)}">{_check_svg()}<p>{_t(x)}</p></div>'
                    for i, x in enumerate(items))
    return (f'<section id="target" class="ds-sec"><div class="ds-in">'
            + _head("FOR YOU", cp.get("targetTitle") or "이런 학생에게 추천합니다")
            + f'<div class="ds-grid ds-g2" style="max-width:920px;margin:0 auto">{cards}</div></div></section>')


def _parse_reviews(cp):
    out = []
    for r in cp.get("reviews", []) or []:
        if isinstance(r, dict):
            out.append([str(r.get("quote", r.get("text", ""))), str(r.get("name", "수강생")), str(r.get("badge", ""))])
        elif isinstance(r, (list, tuple)) and r:
            row = list(r) + ["", ""]
            out.append([str(row[0]), str(row[1]), str(row[2])])
    return [x for x in out if x[0].strip()]

def sec_reviews(d, cp, T):
    reviews = _parse_reviews(cp)
    if not reviews:
        return ""
    label = d["purpose_label"] or d["subject"]
    cards = "".join(
        f'<div class="ds-card ds-quote rv d{min(i+1,4)}"><div class="ds-stars">★★★★★</div>'
        f'<p style="margin-top:14px">{_t(txt)}</p>'
        f'<div class="ds-meta"><span>{_t(nm)}</span><span>{_t(bd)}</span></div></div>'
        for i, (txt, nm, bd) in enumerate(reviews[:6]))
    g = "ds-g3" if len(reviews) % 3 == 0 else "ds-g2"
    sample_note = ('<p class="ds-sample">※ AI가 만든 예시 후기입니다. 게시 전 실제 수강평으로 교체하세요. '
                   '(왼쪽 \'문구 직접 편집 → 수강평\'에서 교체하면 이 안내는 사라집니다)</p>'
                   if cp.get("_reviews_sample") and not st.session_state.get("_exporting") else "")
    return (f'<section id="reviews" class="ds-sec bg2"><div class="ds-in">'
            + _head("REAL REVIEW", cp.get("reviewsTitle") or f"수강생이 말하는 [[{label}]]")
            + f'<div class="ds-grid {g}">{cards}</div>{sample_note}</div></section>')


def sec_faq(d, cp, T):
    faqs = []
    for item in cp.get("faqs", []) or []:
        if isinstance(item, dict):
            faqs.append([item.get("question", item.get("q", "")), item.get("answer", item.get("a", ""))])
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            faqs.append([str(item[0]), str(item[1])])
    faqs = [f for f in faqs if str(f[0]).strip()]
    if not faqs:
        return ""
    rows = "".join(f'<details{" open" if i == 0 else ""}><summary><b>Q</b><span>{_t(q)}</span></summary>'
                   f'<div class="a">{_t(a)}</div></details>' for i, (q, a) in enumerate(faqs))
    return (f'<section id="faq" class="ds-sec"><div class="ds-in">'
            + _head("FAQ", cp.get("faqTitle") or "자주 묻는 질문")
            + f'<div class="ds-faq rv">{rows}</div></div></section>')


def sec_cta(d, cp, T):
    tt    = cp.get("ctaTitle") or f"{d['purpose_label'] or d['subject']}, 지금 시작하세요"
    sub   = cp.get("ctaSub", "")
    cc    = cp.get("ctaCopy") or "수강신청 하기"
    badge = cp.get("ctaBadge", "")
    ct    = _cta_text_color(T)
    title_html = _t(tt).replace('class="hl"', 'class="hl" style="color:inherit;text-decoration:underline;text-underline-offset:.18em"')
    return (
        f'<section id="cta" class="ds-cta" style="background:{T["cta"]};--text:{ct["txt"]};--t70:{ct["txt70"]};--c1:{ct["btn_bg"]};--on-c1:{ct["btn_col"]}">'
        f'<div class="ds-in rv">'
        + (f'<div class="ds-eyebrow" style="color:{ct["txt"]}">{_t(badge)}</div><br>' if badge else "")
        + f'<h2 class="ds-h2" style="color:{ct["txt"]};font-size:clamp(28px,4vw,48px)">{title_html}</h2>'
        + (f'<p class="ds-sub" style="color:{ct["txt70"]}">{_t(sub)}</p>' if sub else "")
        + f'<div class="ds-btns" style="justify-content:center;margin-top:36px"><a class="ds-btn" href="#">{_t(cc)}</a></div>'
        + '</div></section>')


DEFAULT_NOTICE = """본 강좌의 수강 기간, 교재 배송 일정은 수강신청 페이지의 안내를 따릅니다.
이벤트 혜택은 대성마이맥 회원 정보 기준으로 지급되며, 부정 참여 시 지급이 취소될 수 있습니다.
이벤트 내용은 회사 사정에 따라 사전 고지 없이 변경 또는 조기 종료될 수 있습니다.
경품의 제세공과금은 대성마이맥이 부담합니다. (해당 시)"""

def sec_notice(d, cp, T):
    raw = st.session_state.get("notice_text") or DEFAULT_NOTICE
    items = [x.strip(" -•\t") for x in raw.splitlines() if x.strip()]
    if not items:
        return ""
    lis = "".join(f"<li>{_html.escape(x)}</li>" for x in items)
    return (f'<section id="notice" class="ds-notice"><div class="ds-in">'
            f'<h4>유의사항</h4><ul>{lis}</ul></div></section>')

def sec_video(d, cp, T):
    """[v8] OT 영상 섹션"""
    v_url = cp.get("videoUrl", "")
    m = re.search(r'(?:youtu\.be/|v=|embed/|shorts/)([A-Za-z0-9_-]{11})', v_url or "")
    v_url = f"https://www.youtube.com/embed/{m.group(1)}" if m else ""   # 일반 유튜브 링크도 자동 변환
    body = (f'<iframe src="{v_url}" title="OT 영상" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
            if v_url else '<span>사이드바에 유튜브 링크를 넣으면 이 자리에 영상이 들어갑니다</span>')
    label = d["purpose_label"] or d["subject"]
    return (f'<section id="video" class="ds-sec"><div class="ds-in">'
            + _head(cp.get("videoTag") or "OFFICIAL TRAILER", cp.get("videoTitle") or f"[[{label}]] 오리엔테이션", cp.get("videoSub", ""))
            + f'<div class="ds-video rv" style="max-width:920px;margin:0 auto">{body}</div></div></section>')

# ══════════════════════════════════════════════════════
# [v8] 이벤트 · 기획전 섹션 — 디자인 시스템 적용 + 지어낸 기본값(‘D-30’, ‘최대 30%’, ‘성적 보장’) 제거
# ══════════════════════════════════════════════════════
def _info_table(rows) -> str:
    trs = "".join(
        f'<div style="display:grid;grid-template-columns:140px 1fr;border-bottom:1px solid var(--bd)">'
        f'<div style="padding:16px 18px;background:var(--text);color:var(--bg);font-weight:800;font-size:14px">{_t(k)}</div>'
        f'<div style="padding:16px 20px;font-weight:600;color:var(--text);font-size:15px">{_t(v)}</div></div>'
        for k, v in rows)
    return f'<div class="rv" style="max-width:760px;margin:0 auto;border-top:2px solid var(--text)">{trs}</div>'

def sec_event_overview(d, cp, T):
    rows = []
    for row in cp.get("eventDetails") or []:
        if isinstance(row, (list, tuple)):
            r = [str(x) for x in row]
            if len(r) >= 3: rows.append((r[1], r[2]))
            elif len(r) == 2: rows.append((r[0], r[1]))
    if not rows:
        rows = [("이벤트 기간", st.session_state.get("event_info") or "[기간 입력]"), ("참여 대상", "[대상 입력]"), ("당첨자 발표", "[발표일 입력]")]
    return (f'<section id="event-overview" class="ds-sec"><div class="ds-in">'
            + _head("EVENT", cp.get("eventTitle") or "이벤트 안내", cp.get("eventDesc", ""))
            + _info_table(rows) + '</div></section>')

def _benefit_cards(items) -> str:
    out = ""
    for i, b in enumerate(items):
        if not isinstance(b, dict):
            continue
        badge = b.get("badge", "")
        out += (f'<div class="ds-card rv d{min(i+1,4)}"><div style="display:flex;justify-content:space-between;align-items:center">'
                f'<span class="ds-num">{i+1:02d}</span>'
                + (f'<span class="ds-chip" style="color:var(--c1);border-color:var(--c1)">{_t(badge)}</span>' if badge else "")
                + f'</div><h3>{_t(b.get("title",""))}</h3><p>{_t(b.get("desc",""))}</p></div>')
    return out

def sec_event_benefits(d, cp, T):
    items = [b for b in (cp.get("eventBenefits") or []) if isinstance(b, dict) and b.get("title")]
    if not items:
        return ""
    g = "ds-g3" if len(items) == 3 else "ds-g2"
    return (f'<section id="event-benefits" class="ds-sec bg2"><div class="ds-in">'
            + _head("BENEFIT", cp.get("benefitsTitle") or "참여 혜택")
            + f'<div class="ds-grid {g}">{_benefit_cards(items)}</div></div></section>')

def sec_event_deadline(d, cp, T):
    msg = cp.get("deadlineMsg", "")
    if not msg and not cp.get("deadlineTitle"):
        return ""
    ct = _cta_text_color(T)
    return (f'<section id="event-deadline" class="ds-cta" style="background:{T["cta"]};--text:{ct["txt"]};--t70:{ct["txt70"]};--c1:{ct["btn_bg"]};--on-c1:{ct["btn_col"]}">'
            f'<div class="ds-in rv"><div class="ds-eyebrow" style="color:{ct["txt"]}">NOTICE</div><br>'
            f'<h2 class="ds-h2" style="color:{ct["txt"]}">{_t(cp.get("deadlineTitle") or "마감 안내")}</h2>'
            f'<p class="ds-sub" style="color:{ct["txt70"]}">{_t(msg)}</p>'
            f'<div class="ds-btns" style="justify-content:center;margin-top:32px"><a class="ds-btn" href="#cta">{_t(cp.get("ctaCopy") or "이벤트 참여하기")}</a></div>'
            f'</div></section>')

def sec_fest_hero(d, cp, T):
    t   = cp.get("festHeroTitle") or f"{d['subject']} 기획전"
    cc  = cp.get("festHeroCopy", "")
    sub = cp.get("festHeroSub", "")
    bg_url = cp.get("bg_photo_url", "")
    style = (f"background:linear-gradient(180deg,rgba(0,0,0,.45),rgba(0,0,0,.72)),url('{bg_url}') center/cover no-repeat;--text:#fff;--t70:rgba(255,255,255,.82);"
             if bg_url else "background:radial-gradient(70% 55% at 50% 0%,color-mix(in srgb,var(--c1) 16%,transparent),transparent 70%),var(--bg);")
    stats = "".join(f'<div><div style="font-family:var(--fd),var(--fk);font-size:32px;font-weight:900;color:var(--c1)">{_t(a)}</div>'
                    f'<div style="font-size:13px;color:var(--t70);margin-top:4px">{_t(b)}</div></div>'
                    for a, b in (cp.get("festHeroStats") or []) if str(a).strip())
    return (f'<section id="fest-hero" class="ds-sec" style="min-height:min(86vh,820px);display:flex;align-items:center;{style}">'
            f'<div class="ds-in rv" style="text-align:center;width:100%">'
            f'<div class="ds-badge">{_t(d["subject"])} 기획전</div>'
            + (f'<p class="ds-kicker">{_t(cc)}</p>' if cc else "")
            + f'<h1 class="ds-wordmark st" style="font-size:clamp(48px,8vw,112px)">{_t(t)}</h1>'
            + (f'<p class="ds-lead" style="max-width:680px;margin-left:auto;margin-right:auto">{_t(sub)}</p>' if sub else "")
            + (f'<div style="display:flex;gap:56px;justify-content:center;margin-top:48px">{stats}</div>' if stats else "")
            + '</div></section>')

def sec_fest_lineup(d, cp, T):
    lineup = [l for l in (cp.get("festLineup") or []) if isinstance(l, dict) and l.get("name")]
    if not lineup:
        return ""
    cards = "".join(
        f'<div class="ds-card rv d{min(i+1,4)}" style="text-align:center">'
        f'<div style="width:96px;height:96px;border-radius:50%;margin:0 auto 18px;background:var(--bg3);border:1px solid var(--bd);'
        f'display:flex;align-items:center;justify-content:center;font-size:12px;color:var(--t45)">사진</div>'
        + (f'<span class="ds-chip">{_t(l.get("tag",""))}</span>' if l.get("tag") else "")
        + f'<h3>{_t(l.get("name",""))}</h3><p>{_t(l.get("tagline",""))}</p></div>'
        for i, l in enumerate(lineup))
    g = "ds-g4" if len(lineup) >= 4 else "ds-g3" if len(lineup) == 3 else "ds-g2"
    return (f'<section id="fest-lineup" class="ds-sec bg2"><div class="ds-in">'
            + _head("LINE UP", cp.get("festLineupTitle") or "강사 라인업", cp.get("festLineupSub", ""))
            + f'<div class="ds-grid {g}">{cards}</div></div></section>')

def sec_fest_benefits(d, cp, T):
    items = [b for b in (cp.get("festBenefits") or []) if isinstance(b, dict) and b.get("title")]
    if not items:
        return ""
    g = "ds-g3" if len(items) == 3 else "ds-g2"
    return (f'<section id="fest-benefits" class="ds-sec"><div class="ds-in">'
            + _head("BENEFIT", cp.get("festBenefitsTitle") or "기획전 혜택")
            + f'<div class="ds-grid {g}">{_benefit_cards(items)}</div></div></section>')

def sec_fest_cta(d, cp, T):
    tmp = dict(cp)
    tmp["ctaTitle"] = cp.get("festCtaTitle") or f"{d['subject']} 기획전, 지금 신청하세요"
    tmp["ctaSub"]   = cp.get("festCtaSub", "")
    tmp["ctaCopy"]  = "기획전 통합 신청"
    tmp["ctaBadge"] = ""
    return sec_cta(d, tmp, T).replace('id="cta"', 'id="fest-cta"', 1)

# ═══════════════════════════════════════════════════════
# SB 시트 생성
# ═══════════════════════════════════════════════════════
def generate_sb_sheet(cp: dict, ordered_secs: list) -> str:
    LAYOUT_NAMES = {   # [v8] 레이아웃 고정 → 디자이너 전달용 이름
        "banner":     ["킥커 + 워드마크 + 설명 (키비주얼 있으면 좌우 분할)"],
        "why":        ["THE PROBLEM — 헤드라인 + 증상 카드 3개"],
        "intro":      ["THE SOLUTION — 좌: 정체 선언 / 우: 설명"],
        "video":      ["OT 영상 16:9"],
        "curriculum": ["ROADMAP — 단계 카드 가로 배열"],
        "target":     ["체크 카드 2열"],
        "reviews":    ["후기 카드 그리드"],
        "faq":        ["아코디언 1열"],
        "cta":        ["풀폭 컬러 블록 + 버튼"],
    }

    lines = [
        f"# 📋 스토리보드 시트\n",
        f"| 항목 | 내용 |",
        f"|------|------|",
        f"| 강좌명 | **{st.session_state.purpose_label}** |",
        f"| 강사 | {st.session_state.instructor_name or '—'} |",
        f"| 과목 | {st.session_state.subject} |",
        f"| 목적 | {st.session_state.purpose_type} |",
        f"| 어조 | {st.session_state.copy_tone} |",
        f"\n---\n",
    ]

    for i, sec_id in enumerate(ordered_secs):
        if sec_id == "custom_section":
            continue

        sec_label = SEC_LABELS.get(sec_id, sec_id)

        # 레이아웃 이름 결정
        layout_name = "자동 결정"
        if sec_id in LAYOUT_NAMES:
            names = LAYOUT_NAMES[sec_id]
            text_hash = sum(ord(c) for c in str(cp.get("bannerTitle", "")) + sec_id)
            layout_name = names[text_hash % len(names)]

        lines.append(f"## {i+1:02d}. {sec_label}")
        lines.append(f"> **레이아웃 컨셉:** {layout_name}\n")

        # 섹션별 핵심 카피 추출
        if sec_id == "banner":
            lines.append(f"- **킥커:** {cp.get('bannerKicker', '—')}")
            lines.append(f"- **메인 카피:** {cp.get('bannerTitle', '—')}")
            lines.append(f"- **서브 뱃지:** {cp.get('bannerSub', '—')}")
            lines.append(f"- **리드 문구:** {(cp.get('bannerLead') or '')[:80]}{'...' if len(cp.get('bannerLead') or '') > 80 else ''}")
            lines.append(f"- **CTA 버튼:** {cp.get('ctaCopy', '—')}")
            lines.append(f"- **영문 슬로건:** {cp.get('brandTagline', '—')}")
            if cp.get("bannerVisual"):
                lines.append(f"\n🎥 **비주얼 디렉션:** {cp.get('bannerVisual')}")

        elif sec_id == "intro":
            lines.append(f"- **섹션 제목:** {cp.get('introTitle', '—')}")
            lines.append(f"- **소개 본문:** {(cp.get('introDesc') or '')[:80]}...")
            lines.append(f"- **한줄 약력:** {cp.get('introBio', '—')}")
            if cp.get("introVisual"):
                lines.append(f"\n🎥 **비주얼 디렉션:** {cp.get('introVisual')}")

        elif sec_id == "why":
            lines.append(f"- **섹션 제목:** {cp.get('whyTitle', '—')}")
            lines.append(f"- **서브:** {cp.get('whySub', '—')}")
            for r in (cp.get("whyReasons") or []):
                if len(r) >= 3:
                    lines.append(f"  - 📌 **{r[1]}** — {str(r[2])[:60]}...")
            if cp.get("whyVisual"):
                lines.append(f"\n🎥 **비주얼 디렉션:** {cp.get('whyVisual')}")

        elif sec_id == "curriculum":
            lines.append(f"- **섹션 제목:** {cp.get('curriculumTitle', '—')}")
            for s in (cp.get("curriculumSteps") or []):
                if len(s) >= 3:
                    lines.append(f"  - STEP {s[0]} **{s[1]}** ({s[3] if len(s)>3 else '—'}): {str(s[2])[:50]}...")

        elif sec_id == "target":
            lines.append(f"- **섹션 제목:** {cp.get('targetTitle', '—')}")
            for t in (cp.get("targetItems") or []):
                lines.append(f"  - ✔ {str(t)[:60]}")

        elif sec_id == "reviews":
            for rv in (cp.get("reviews") or [])[:3]:
                if isinstance(rv, (list, tuple)) and len(rv) >= 3:
                    lines.append(f"  - ⭐ \"{str(rv[0])[:50]}...\" — {rv[1]} ({rv[2]})")

        elif sec_id == "cta":
            lines.append(f"- **CTA 제목:** {cp.get('ctaTitle', '—')}")
            lines.append(f"- **서브 문구:** {cp.get('ctaSub', '—')}")
            lines.append(f"- **버튼:** {cp.get('ctaCopy', '—')}")
            lines.append(f"- **뱃지:** {cp.get('ctaBadge', '—')}")

        elif sec_id == "faq":
            for fq in (cp.get("faqs") or [])[:3]:
                if len(fq) >= 2:
                    lines.append(f"  - Q: {fq[0]}")

        lines.append("\n---\n")

    return "\n".join(lines)
    
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
            f"[\"이벤트 기간\",\"{st.session_state.get('event_info') or '[기간 입력]'}\"],"
            f"[\"이벤트 대상\",\"강좌 수강생\"],"
            f"[\"당첨자 발표\",\"[발표일 입력]\"],"
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
    t    = strip_hanja(cp.get("methodTitle", f"{d['purpose_label']} 학습법"))
    sub  = strip_hanja(cp.get("methodSub",   "이 방식으로 접근하면 지문이 완전히 달리 보입니다"))
    methods_raw = cp.get("methodSteps",[])
    ip = st.session_state.get("inst_profile") or {}
    plabel = st.session_state.get("purpose_label", "")
    
    # ✅ 핵심 수정: 현재 브랜드명과 일치하는 메서드만 사용
    all_methods = [strip_hanja(m) for m in (ip.get("signatureMethods") or []) if m and m not in ("없음","")]
    plabel_lower = plabel.replace(" ", "").lower()
    sig = [m for m in all_methods if m.replace(" ","").lower() in plabel_lower or plabel_lower in m.replace(" ","").lower()]
    # 일치하는 메서드가 없으면 빈 리스트 (다른 커리큘럼명 사용 금지)
    
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
        return ""   # [v8] 강좌 정보가 없으면 섹션 자체를 숨김

    title   = strip_hanja(c.get("courseTitle", "강좌 소개"))
    sub     = strip_hanja(c.get("courseSub", ""))
    desc    = strip_hanja(c.get("courseDesc", ""))
    points  = c.get("coursePoints", [])
    dur     = strip_hanja(c.get("courseDuration", ""))
    level   = strip_hanja(c.get("courseLevel", ""))
    tags    = [strip_hanja(t) for t in c.get("courseTag", [])]

    v = (sum(ord(c) for c in str(title or "") + str(sub or "")) % 3) + 1
    
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
        return ""   # [v8] 교재 정보가 없으면 섹션 자체를 숨김

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
    elif methods:
        # ✅ 현재 브랜드명과 일치하는 메서드만 사용
        plabel_clean = plabel.replace(" ", "").lower()
        matched = [m for m in methods if m.replace(" ","").lower() in plabel_clean or plabel_clean in m.replace(" ","").lower()]
        method_flow = " → ".join(matched[:3]) if matched else plabel
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
# HTML 빌더 [v8]
#  - 사선 구분선·고정 내비·다크모드 토글·'📸 저장' 버튼 제거(다운로드한 HTML에도 박혀 있었음)
#  - 파티클·글리치 같은 효과는 사이드바 '배경 효과' 체크 시에만
#  - 한글 폰트 Pretendard 통일, 테마 폰트는 워드마크/영문 라벨 전용
# ══════════════════════════════════════════════════════
def _font_vars(T: dict) -> str:
    """테마 --fh(영문 디스플레이 폰트)를 --fd로 옮기고, --fh는 한글 폰트로 바꿈 + 포인트색 위 글자색 계산"""
    v = T["vars"].replace("--fh:", "--fd:")
    v += "--fh:var(--fk);"
    if "--on-c1:" not in v:
        m = re.search(r'--c1:\s*(#[0-9A-Fa-f]{3,6})', v)
        on = "#0A0A0A" if (m and _hex_luminance(m.group(1)) > 0.45) else "#FFFFFF"
        v += f"--on-c1:{on};"
    return v

RENDERERS = {}   # build_html 안에서 채움 (사이드바에서 섹션 목록 필터용)

def build_html(secs: list, exporting: bool = False) -> str:
    st.session_state["_exporting"] = exporting
    T  = get_theme()
    cp = dict(st.session_state.custom_copy or {})
    if st.session_state.get("uploaded_bg_b64"):
        cp["bg_photo_url"] = st.session_state.uploaded_bg_b64
    elif st.session_state.bg_photo_url:
        cp["bg_photo_url"] = st.session_state.bg_photo_url
    d = {"name": st.session_state.instructor_name or "",
         "subject": st.session_state.subject,
         "purpose_label": st.session_state.purpose_label,
         "target": st.session_state.target}
    if st.session_state.concept == "custom" and st.session_state.custom_theme:
        T["heroStyle"] = st.session_state.custom_theme.get("heroStyle", "typographic")
    else:
        T["heroStyle"] = THEMES.get(st.session_state.concept, {}).get("heroStyle", "typographic")
    mp = {
        "banner": sec_banner, "intro": sec_intro, "why": sec_why, "curriculum": sec_curriculum,
        "target": sec_target, "reviews": sec_reviews, "faq": sec_faq, "cta": sec_cta, "notice": sec_notice,
        "video": sec_video, "before_after": sec_before_after, "method": sec_method, "package": sec_package,
        "grade_stats": sec_grade_stats,
        "event_overview": sec_event_overview, "event_benefits": sec_event_benefits,
        "event_deadline": sec_event_deadline, "fest_hero": sec_fest_hero,
        "fest_lineup": sec_fest_lineup, "fest_benefits": sec_fest_benefits,
        "fest_cta": sec_fest_cta, "custom_section": sec_custom,
        "course_intro": sec_course_intro, "textbook_sale": sec_textbook_sale,
        "instructor_philosophy": sec_instructor_philosophy,
    }
    RENDERERS.update(mp)
    sections_html = []
    for s in secs:
        if s in mp:
            try:
                h = mp[s](d, cp, T)
            except Exception as e:     # 한 섹션 오류가 페이지 전체를 깨뜨리지 않도록
                h = "" if exporting else f'<div style="padding:16px;color:#c00;font-size:12px">[{s}] 렌더 오류: {_html.escape(str(e))}</div>'
            if h:
                sections_html.append(h)
    body = "\n".join(sections_html)
    # 레거시 섹션에 남은 [[강조]]도 일괄 변환
    body = re.sub(r'\[\[(.+?)\]\]', r'<span class="hl">\1</span>', body)

    ttl = strip_hanja(str(cp.get("bannerTitle", cp.get("festHeroTitle", d["purpose_label"]))))
    ttl = re.sub(r'\[\[|\]\]', '', ttl)
    fx = ""
    if st.session_state.get("fx_on"):
        concept_key = st.session_state.concept if st.session_state.concept != "custom" else "custom"
        fx = _particle_js(T.get("particle", "none")) + _theme_fx(concept_key)
    dark_card = ".card{background:var(--bg2)!important}" if T["dark"] else ""
    return (
        '<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"/>'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0"/>'
        f'<title>{_html.escape(d["name"])} {d["subject"]} · {_html.escape(ttl)}</title>'
        '<link rel="preconnect" href="https://fonts.googleapis.com"/>'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>'
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"/>'
        f'<link href="{T["fonts"]}" rel="stylesheet"/>'
        f'<style>:root{{{_font_vars(T)}}}{BASE_CSS}{T["extra_css"]}{dark_card}{DS_CSS}</style>'
        f'</head><body>{body}{fx}'
        '<script>'
        'const ro=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){e.target.classList.add("on");ro.unobserve(e.target);}});},{threshold:.06,rootMargin:"0px 0px -40px 0px"});'
        'document.querySelectorAll(".rv,.rv-left,.rv-right,.reveal-text").forEach(el=>ro.observe(el));'
        '</script></body></html>'
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


def _model_quality_note():
    m = st.session_state.get("_last_model", "")
    if m:
        st.caption(f"사용 모델: `{m}`")
        if m != GROQ_MODELS[0]:
            st.warning("메인 모델(gpt-oss-120b)이 응답하지 않아 보조 모델로 생성됐어요. 문구 품질이 떨어질 수 있으니 잠시 후 다시 생성해 보세요.")

# ── [v11] 구형 생성기(강좌 소개·교재·기타 섹션)도 품질 검사 + 교정 패스를 거치도록 감쌈 ──
def _wrap_quality(fn):
    def inner(*a, **k):
        r = fn(*a, **k)
        if isinstance(r, dict) and r:
            plabel = st.session_state.get("purpose_label", "")
            r = polish_copy(r, build_copy_brief(st.session_state.get("_last_ctx", "")))
            r = proofread_copy(r, plabel)
        return r
    return inner
gen_course_copy   = _wrap_quality(gen_course_copy)
gen_textbook_copy = _wrap_quality(gen_textbook_copy)
gen_custom_sec    = _wrap_quality(gen_custom_sec)

# ══════════════════════════════════════════════════════════════════════
# [v9] 📝 강좌 특징 HTML 모드 — 관리자 페이지 '강좌 특징' 영역 삽입용
#
#  구조:  원고 ──(AI: 구조화·오탈자 교정만)──▶ 편집용 마크업 ──(파이썬: 고정 디자인)──▶ 인라인 CSS HTML
#   · 디자인은 AI가 아니라 코드가 그리므로, 한 번 승인된 디자인은 매번 똑같이 나옵니다.
#   · 마크업은 화면에서 직접 고칠 수 있고, 부분 수정 요청 시 해당 챕터만 바뀝니다.
#   · 원고에 없는 숫자/문장, 빠진 문장을 자동으로 찾아 알려줍니다.
# ══════════════════════════════════════════════════════════════════════
import html as _fhtml

FEAT_DEFAULT_COLORS = {
    "main": "#263A53",   # Deep Navy — 포인트(제목·구분선)
    "body": "#202B38",   # Charcoal — 본문
    "sub":  "#657182",   # Slate Gray — 보조
    "bg":   "#F5F7FA",   # Soft Gray — 배경 박스
    "hl":   "#E4EAF2",   # 하이라이트
}
FEAT_POINT_PRESETS = {
    "기본 네이비": "#263A53",
    "딥 그린": "#24493F",
    "버건디": "#5B2A34",
    "딥 퍼플": "#3D3460",
    "다크 틸": "#1F4B57",
    "웜 브라운": "#4A3B2C",
}
FEAT_FONT = "Arial, sans-serif"

FEAT_MARKUP_GUIDE = """\
@title 강좌명
@subtitle 서브 타이틀
@intro 도입 문단 (선택)

# 챕터 제목            → 번호 + 구분선이 붙는 챕터
## 소제목
일반 문장은 그대로 쓰면 문단이 됩니다. (빈 줄로 문단 구분)
> 핵심 메시지          → 라인 박스
>> 핵심 메시지         → 배경 박스
- 항목                 → 글머리표 목록
1. 항목                → 번호 목록
[카드] 제목 | 설명 | 부가 정보   → 연속된 [카드] 줄이 2~3단 박스로
| 구분 | 내용 |                  → 표 (첫 줄은 머리글)
**굵게**   ==하이라이트==  (하이라이트는 전체 2~3곳만)"""


# ── 색상 유틸 ──────────────────────────────────────────────
def _feat_mix(hex_color: str, ratio: float, base: str = "#FFFFFF") -> str:
    """hex_color를 base와 섞음 (ratio = hex_color 비율)"""
    def _rgb(h):
        h = h.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    try:
        a, b = _rgb(hex_color), _rgb(base)
    except Exception:
        return base
    return "#" + "".join(f"{round(x * ratio + y * (1 - ratio)):02X}" for x, y in zip(a, b))

def feat_palette(point: str) -> dict:
    c = dict(FEAT_DEFAULT_COLORS)
    point = (point or "").strip()
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", point) and point.upper() != c["main"].upper():
        c["main"] = point.upper()
        c["hl"] = _feat_mix(point, 0.14)          # 포인트 컬러에 맞춘 연한 하이라이트
    c["line"] = "#DDE2E8"
    c["card_bd"] = "#D5DBE3"
    return c


# ── 마크업 → 블록 ──────────────────────────────────────────
def feat_parse(markup: str) -> dict:
    doc = {"title": "", "subtitle": "", "intro": [], "chapters": []}
    cur = None            # 현재 챕터
    blocks = None         # 현재 블록 목록 (챕터 전이면 intro_blocks)
    intro_blocks = []
    para = []

    def flush_para():
        nonlocal para
        if para:
            blocks.append({"type": "p", "text": " ".join(para).strip()})
            para = []

    blocks = intro_blocks
    lines = (markup or "").replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        if not s:
            flush_para(); i += 1; continue
        if s.startswith("@title"):
            doc["title"] = s[6:].strip(); i += 1; continue
        if s.startswith("@subtitle"):
            doc["subtitle"] = s[9:].strip(); i += 1; continue
        if s.startswith("@intro"):
            flush_para()
            intro_blocks.append({"type": "p", "text": s[6:].strip()}); i += 1; continue
        if s.startswith("## "):
            flush_para()
            blocks.append({"type": "h4", "text": s[3:].strip()}); i += 1; continue
        if s.startswith("# "):
            flush_para()
            cur = {"title": s[2:].strip(), "blocks": []}
            doc["chapters"].append(cur)
            blocks = cur["blocks"]; i += 1; continue
        if s.startswith(">>"):
            flush_para()
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">>"):
                buf.append(lines[i].strip()[2:].strip()); i += 1
            blocks.append({"type": "bgbox", "text": "<br>".join(buf)}); continue
        if s.startswith(">"):
            flush_para()
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">") and not lines[i].strip().startswith(">>"):
                buf.append(lines[i].strip()[1:].strip()); i += 1
            blocks.append({"type": "linebox", "text": "<br>".join(buf)}); continue
        if re.match(r"^[-•·]\s+", s):
            flush_para()
            items = []
            while i < len(lines) and re.match(r"^[-•·]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-•·]\s+", "", lines[i].strip())); i += 1
            blocks.append({"type": "ul", "items": items}); continue
        if re.match(r"^\d+[.)]\s+", s):
            flush_para()
            items = []
            while i < len(lines) and re.match(r"^\d+[.)]\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+[.)]\s+", "", lines[i].strip())); i += 1
            blocks.append({"type": "ol", "items": items}); continue
        if s.startswith("[카드]"):
            flush_para()
            cards = []
            while i < len(lines) and lines[i].strip().startswith("[카드]"):
                parts = [p.strip() for p in lines[i].strip()[4:].split("|")]
                cards.append((parts + ["", "", ""])[:3]); i += 1
            blocks.append({"type": "cards", "items": cards}); continue
        if s.startswith("|"):
            flush_para()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in row if c):   # |---|---| 구분줄 무시
                    rows.append(row)
                i += 1
            if rows:
                blocks.append({"type": "table", "rows": rows})
            continue
        para.append(s); i += 1
    flush_para()
    doc["intro"] = intro_blocks
    return doc


# ── 인라인 서식 (**굵게**, ==하이라이트==) ──────────────────
def _feat_inline(text: str, c: dict, allow_emph: bool = True) -> str:
    keep_br = text.split("<br>")
    out = []
    for t in keep_br:
        t = _fhtml.escape(t, quote=False)
        if allow_emph:
            t = re.sub(r"==(.+?)==", rf'<span style="background-color:{c["hl"]};padding:1px 0;">\1</span>', t)
            t = re.sub(r"\*\*(.+?)\*\*", rf'<strong style="font-weight:bold;color:{c["body"]};">\1</strong>', t)
        else:   # 정보 전달 영역(표·카드 본문): 강조 표시는 지우고 글자만 남김
            t = re.sub(r"==(.+?)==", r"\1", t)
            t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
        out.append(t)
    return "<br>".join(out)


# ── 블록 → 인라인 CSS HTML ─────────────────────────────────
def feat_render(doc: dict, point: str = "#263A53", max_width: int = 860, mobile_stack: bool = False) -> str:
    c = feat_palette(point)
    F = f"font-family:{FEAT_FONT};"
    P = f"{F}font-size:16px;line-height:1.8;color:{c['body']};margin:0 0 14px 0;word-break:keep-all;"

    def render_block(b):
        t = b["type"]
        if t == "p":
            return f'<p style="{P}">{_feat_inline(b["text"], c)}</p>'
        if t == "h4":
            return (f'<h4 style="{F}font-size:18px;font-weight:bold;color:{c["main"]};line-height:1.5;'
                    f'margin:28px 0 10px 0;">{_feat_inline(b["text"], c, False)}</h4>')
        if t == "linebox":
            return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
                    f'style="width:100%;border-collapse:collapse;margin:20px 0;"><tr>'
                    f'<td style="{F}border:1px solid {c["main"]};border-left:4px solid {c["main"]};padding:18px 22px;'
                    f'font-size:17px;line-height:1.7;color:{c["body"]};font-weight:bold;word-break:keep-all;">'
                    f'{_feat_inline(b["text"], c)}</td></tr></table>')
        if t == "bgbox":
            return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
                    f'style="width:100%;border-collapse:collapse;margin:20px 0;"><tr>'
                    f'<td style="{F}background-color:{c["bg"]};padding:22px 26px;font-size:16px;line-height:1.8;'
                    f'color:{c["body"]};word-break:keep-all;">{_feat_inline(b["text"], c)}</td></tr></table>')
        if t in ("ul", "ol"):
            tag = t
            lis = "".join(f'<li style="{F}font-size:16px;line-height:1.8;color:{c["body"]};margin:0 0 6px 0;">'
                          f'{_feat_inline(x, c)}</li>' for x in b["items"])
            return f'<{tag} style="{F}margin:0 0 16px 0;padding-left:22px;">{lis}</{tag}>'
        if t == "cards":
            items = b["items"]
            n = len(items)
            cols = 2 if n in (2, 4) else 3 if n >= 3 else 1
            def card(ci):
                title, desc, meta = ci
                return (f'<div style="{F}font-size:17px;font-weight:bold;color:{c["main"]};line-height:1.45;margin:0 0 10px 0;">{_feat_inline(title, c, False)}</div>'
                        + (f'<div style="{F}font-size:15px;line-height:1.75;color:{c["body"]};">{_feat_inline(desc, c, False)}</div>' if desc else "")
                        + (f'<div style="{F}font-size:13px;line-height:1.6;color:{c["sub"]};margin-top:12px;padding-top:10px;border-top:1px solid {c["line"]};">{_feat_inline(meta, c, False)}</div>' if meta else ""))
            if mobile_stack:   # 좁은 화면에서 자동으로 세로 정렬 (flex-wrap)
                basis = {1: "100%", 2: "300px", 3: "220px"}[cols]
                cells = "".join(
                    f'<div style="flex:1 1 {basis};box-sizing:border-box;border:1px solid {c["card_bd"]};'
                    f'border-top:3px solid {c["main"]};padding:22px 20px;background-color:#FFFFFF;">{card(ci)}</div>'
                    for ci in items)
                return f'<div style="display:flex;flex-wrap:wrap;gap:12px;margin:20px 0;">{cells}</div>'
            # 기본: 표 구조 (관리자 에디터 호환성 최우선) — 카드 사이는 빈 칸(td)으로 간격
            gap_td = '<td width="12" style="width:12px;border:0;padding:0;font-size:0;">&nbsp;</td>'
            colw = f"{(100 - 2 * (cols - 1)) // cols}%"
            rows_html = ""
            for r in range(0, n, cols):
                row = items[r:r + cols]
                tds = []
                for k in range(cols):
                    if k < len(row):
                        tds.append(f'<td valign="top" width="{colw}" style="width:{colw};vertical-align:top;'
                                   f'border:1px solid {c["card_bd"]};border-top:3px solid {c["main"]};padding:22px 20px;background-color:#FFFFFF;">'
                                   f'{card(row[k])}</td>')
                    else:
                        tds.append(f'<td width="{colw}" style="width:{colw};border:0;"></td>')
                rows_html += "<tr>" + gap_td.join(tds) + "</tr>"
                if r + cols < n:
                    rows_html += f'<tr><td colspan="{2 * cols - 1}" style="height:12px;border:0;padding:0;font-size:0;">&nbsp;</td></tr>'
            return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
                    f'style="width:100%;border-collapse:collapse;margin:20px 0;table-layout:fixed;">'
                    f'{rows_html}</table>')
        if t == "table":
            rows = b["rows"]
            ncol = max(len(r) for r in rows)
            head = rows[0] + [""] * (ncol - len(rows[0]))
            ths = "".join(f'<th style="{F}background-color:{c["main"]};color:#FFFFFF;font-size:15px;font-weight:bold;'
                          f'padding:12px 14px;border:1px solid {c["main"]};text-align:center;">{_feat_inline(h, c, False)}</th>' for h in head)
            trs = ""
            for r in rows[1:]:
                r = r + [""] * (ncol - len(r))
                trs += "<tr>" + "".join(
                    f'<td style="{F}font-size:15px;line-height:1.7;color:{c["body"]};padding:12px 14px;border:1px solid {c["card_bd"]};'
                    f'{"background-color:" + c["bg"] + ";font-weight:bold;text-align:center;" if j == 0 else ""}vertical-align:top;">'
                    f'{_feat_inline(x, c, False)}</td>' for j, x in enumerate(r)) + "</tr>"
            return (f'<table width="100%" cellpadding="0" cellspacing="0" border="0" '
                    f'style="width:100%;border-collapse:collapse;margin:18px 0;"><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>')
        return ""

    parts = [f'<div style="{F}max-width:{max_width}px;margin:0 auto;padding:48px 20px 56px 20px;background-color:#FFFFFF;color:{c["body"]};">']
    # 헤더
    if doc.get("subtitle"):
        parts.append(f'<p style="{F}font-size:16px;line-height:1.6;color:{c["sub"]};margin:0 0 8px 0;">{_feat_inline(doc["subtitle"], c, False)}</p>')
    if doc.get("title"):
        parts.append(f'<h2 style="{F}font-size:30px;font-weight:bold;line-height:1.35;color:{c["main"]};margin:0 0 24px 0;">{_feat_inline(doc["title"], c, False)}</h2>')
    parts.append(f'<hr style="border:0;border-top:3px solid {c["main"]};margin:0 0 28px 0;height:0;">')
    for b in doc.get("intro", []):
        parts.append(render_block(b))
    # 챕터
    for idx, ch in enumerate(doc.get("chapters", []), 1):
        parts.append(f'<hr style="border:0;border-top:1px solid {c["line"]};margin:44px 0 32px 0;height:0;">')
        parts.append(f'<p style="{F}font-size:14px;font-weight:bold;color:{c["main"]};margin:0 0 6px 0;">{idx:02d}</p>')
        parts.append(f'<h3 style="{F}font-size:23px;font-weight:bold;line-height:1.4;color:{c["main"]};margin:0 0 18px 0;">{_feat_inline(ch["title"], c, False)}</h3>')
        for b in ch["blocks"]:
            parts.append(render_block(b))
    parts.append("</div>")
    return "\n".join(parts)


def feat_preview_html(fragment: str, title: str) -> str:
    """② 디자인 미리보기 — 관리자 '강좌 특징' 영역과 비슷한 환경(흰 배경, 외부 CSS 없음)"""
    return ('<!DOCTYPE html>\n<html lang="ko">\n<head>\n<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            f'<title>{_fhtml.escape(title or "강좌 특징")} - 디자인 미리보기</title>\n</head>\n'
            '<body style="margin:0;padding:0;background-color:#FFFFFF;">\n'
            '<!-- ▼▼ 관리자 페이지 HTML 탭에 들어가는 부분 (강좌_특징_관리자코드.txt와 동일) ▼▼ -->\n'
            f'{fragment}\n'
            '<!-- ▲▲ 여기까지 ▲▲ -->\n</body>\n</html>\n')


# ── 원고 대비 검사 ────────────────────────────────────────
def _feat_plain(s: str) -> str:
    s = re.sub(r"\*\*|==|\[카드\]|^[#>@\-\d.)\s]+", "", s)
    return re.sub(r"[^\w가-힣]", "", s)

def _feat_bigrams(s: str, n: int = 4) -> set:
    """글자 n-gram 집합 (4글자 단위 — 조사·어미 교정 정도는 통과, 문장 추가·삭제는 잡힘)"""
    s = _feat_plain(s)
    return {s[k:k + n] for k in range(len(s) - n + 1)}

def feat_check(manuscript: str, markup: str) -> dict:
    src_plain = _feat_plain(manuscript)
    src_bi = _feat_bigrams(manuscript)
    res = {"new_numbers": [], "new_lines": [], "missing": [], "hl_count": 0, "bold_count": 0}
    # 원고에 없는 숫자
    src_nums = set(re.findall(r"\d+(?:[.,]\d+)?", manuscript))
    for n in sorted(set(re.findall(r"\d+(?:[.,]\d+)?", markup)) - src_nums):
        # 챕터 자동번호(01, 02)·목록 번호는 제외
        if not re.search(rf"(^|\n)\s*{re.escape(n)}[.)]\s", markup):
            res["new_numbers"].append(n)
    # 원고에서 온 게 아닐 수 있는 문장
    for line in markup.splitlines():
        s = line.strip()
        if not s or s.startswith(("@title", "@subtitle", "#")) or re.fullmatch(r"\|[\s\-:|]+\|", s):
            continue   # 제목·소제목은 원고 단어로 새로 붙이는 게 허용되므로 검사 제외
        txt = re.sub(r"^(#+|>>|>|[-•·]|\d+[.)]|\[카드\]|@intro)\s*", "", s)
        bi = _feat_bigrams(txt)
        if len(bi) >= 6:
            overlap = len(bi & src_bi) / len(bi)
            if overlap < 0.5:
                res["new_lines"].append((txt[:80], round(overlap * 100)))
    # 원고 문장 중 결과에 거의 안 보이는 것 (누락 의심)
    out_bi = _feat_bigrams(markup, 3)
    for sent in re.split(r"(?<=[.!?。,])\s+|\n+", manuscript):
        sent = sent.strip()
        bi = _feat_bigrams(sent, 3)
        if len(bi) >= 6 and len(bi & out_bi) / len(bi) < 0.4:
            res["missing"].append(sent[:90])
    res["hl_count"] = len(re.findall(r"==(.+?)==", markup))
    res["bold_count"] = len(re.findall(r"\*\*(.+?)\*\*", markup))
    return res


# ── AI: 원고 → 마크업 ─────────────────────────────────────
FEAT_SYSTEM_RULES = """당신은 대성마이맥 강좌 상세 페이지의 웹 콘텐츠 에디터입니다.
강좌 소개 원고를 '강좌 특징' 영역용 편집 마크업으로 정리합니다. 디자인은 코드가 하므로 당신은 '구조'와 '최소 교정'만 합니다.

[절대 원칙]
1. 원고의 기획 의도와 핵심 메시지를 유지합니다.
2. 문장 수정은 오탈자, 중복 표현, 문맥 개선으로만 최소화합니다. 문장을 새로 쓰거나 요약해서 없애지 않습니다.
3. 원고에 없는 강좌 구성, 학습 효과, 교재 정보, 숫자, 수식어를 추가하지 않습니다.
4. 원고의 모든 내용이 결과에 들어가야 합니다. 순서는 정보 위계에 맞게 묶는 정도만 조정합니다.
5. 제목·소제목은 원고에 있으면 그대로, 없으면 원고 문장에서 단어를 가져와 짧게 붙입니다(새 주장 금지).

[마크업 문법]
@title 강좌명
@subtitle 서브 타이틀
@intro 도입 문단 (선택, 여러 줄 가능)
# 챕터 제목                 (원고의 큰 덩어리마다 하나. 보통 3~6개)
## 소제목
일반 문단은 그대로 (빈 줄로 구분)
> 핵심 메시지 (라인 박스)   — 챕터의 결론·핵심 문장. 페이지 전체 2~4곳
>> 핵심 메시지 (배경 박스) — 인용·요약·강조할 묶음
- 목록 / 1. 번호 목록
[카드] 제목 | 설명 | 부가정보   — 교재 라인업·단계·구성처럼 나란히 비교할 2~6개 항목
| 머리글 | 머리글 |  다음 줄부터 | 값 | 값 |   — 일정·구성표
**굵게**: 본문의 중요한 문장·핵심 키워드에만 제한적으로 (챕터당 0~2개)
==하이라이트==: 페이지 전체에서 2~3곳만
교재 구성·표·카드 같은 정보 영역에는 굵게·하이라이트를 쓰지 않습니다.
"""

def feat_ai_convert(title: str, subtitle: str, manuscript: str, direction: str, extra: str) -> dict:
    prompt = (
        f"{FEAT_SYSTEM_RULES}\n"
        f"[강좌명] {title}\n[서브 타이틀] {subtitle}\n"
        f"[디자인 방향] {direction or '기본 네이비'}\n"
        f"[추가 요청사항] {extra or '없음'}\n\n"
        f"[강좌 소개 원고]\n<<<\n{manuscript}\n>>>\n\n"
        "아래 JSON 하나만 반환하세요:\n"
        '{"markup": "@title ...\\n@subtitle ...\\n\\n# ...", '
        '"changes": [{"before": "원고 표현", "after": "고친 표현", "reason": "오탈자/중복/문맥"}]}'
    )
    raw = call_ai(prompt, max_tokens=6000, temperature=0.3)
    data = safe_json(raw)
    markup = str(data.get("markup", "")).strip()
    if not markup:
        raise ValueError("AI 응답에 마크업이 비어 있습니다. 다시 시도해주세요.")
    if not re.search(r"^@title", markup, re.M) and title:
        markup = f"@title {title}\n" + (f"@subtitle {subtitle}\n" if subtitle else "") + "\n" + markup
    return {"markup": markup, "changes": data.get("changes") or []}

def feat_split_chapters(markup: str):
    """마크업 → (머리 부분, [챕터 텍스트...])"""
    parts = re.split(r"(?m)^(?=# )", markup)
    head = parts[0] if parts and not parts[0].startswith("# ") else ""
    chapters = [p for p in parts if p.startswith("# ")]
    return head, chapters

def feat_ai_partial(markup: str, target_idx: int, request: str, manuscript: str) -> str:
    """지정한 챕터(또는 머리 부분)만 고치고 나머지는 글자 하나 안 바뀌게 다시 이어 붙임"""
    head, chs = feat_split_chapters(markup)
    target = head if target_idx < 0 else chs[target_idx]
    prompt = (
        f"{FEAT_SYSTEM_RULES}\n"
        "아래 [수정 대상] 마크업 조각만 [수정 요청]대로 고치세요. 요청과 무관한 문장·구조는 그대로 둡니다.\n"
        f"[수정 요청] {request}\n\n[원고 — 사실 확인용]\n<<<\n{manuscript}\n>>>\n\n"
        f"[수정 대상]\n<<<\n{target}\n>>>\n\n"
        'JSON 하나만 반환: {"markup": "고친 조각 전체"}'
    )
    new = str(safe_json(call_ai(prompt, max_tokens=3000, temperature=0.3)).get("markup", "")).strip()
    if not new:
        raise ValueError("수정 결과가 비어 있습니다.")
    if target_idx >= 0 and not new.startswith("# "):
        new = chs[target_idx].splitlines()[0] + "\n" + new
    new = new.rstrip() + "\n\n"
    if target_idx < 0:
        head = new
    else:
        chs[target_idx] = new
    return head + "".join(chs)

def feat_plain_markup(title: str, subtitle: str, manuscript: str) -> str:
    """AI 없이: 원고를 그대로 문단으로 옮긴 기본 마크업 (직접 # > [카드] 등을 붙여 다듬는 용도)"""
    body = "\n\n".join(p.strip() for p in re.split(r"\n\s*\n", manuscript.strip()) if p.strip())
    return f"@title {title}\n@subtitle {subtitle}\n\n{body}\n"


# ── 화면 ──────────────────────────────────────────────────
_FEAT_DEFAULTS = {
    "f_title": "", "f_subtitle": "", "f_manuscript": "", "f_extra": "",
    "f_point": "#263A53", "f_direction": "", "f_markup": "", "f_changes": [],
    "f_maxw": 860, "f_stack": False, "f_approved": False,
}

def render_feature_mode():
    for k, v in _FEAT_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v

    with st.sidebar:
        st.markdown('<div class="sec-hdr">🔑 Groq API</div>', unsafe_allow_html=True)
        if not st.session_state.api_key:
            _k = st.text_input("API Key", type="password", placeholder="gsk_...", key="f_api_in")
            if _k:
                st.session_state.api_key = _k
        else:
            st.caption("✓ API 키 연결됨")

        st.markdown('<div class="sec-hdr">🎨 포인트 컬러</div>', unsafe_allow_html=True)
        preset = st.selectbox("프리셋", ["직접 지정"] + list(FEAT_POINT_PRESETS.keys()),
                              index=1, key="f_preset", disabled=st.session_state.f_approved)
        if preset != "직접 지정":
            st.session_state.f_point = FEAT_POINT_PRESETS[preset]
        st.session_state.f_point = st.color_picker("포인트 컬러", st.session_state.f_point,
                                                   disabled=st.session_state.f_approved or preset != "직접 지정")
        st.caption("본문·배경·보조 컬러는 가이드 고정값(Charcoal #202B38 / Soft Gray #F5F7FA / Slate Gray #657182)")

        st.markdown('<div class="sec-hdr">📐 레이아웃</div>', unsafe_allow_html=True)
        st.session_state.f_maxw = st.slider("최대 너비(px)", 720, 1000, st.session_state.f_maxw, 20,
                                            disabled=st.session_state.f_approved)
        st.session_state.f_stack = st.checkbox("모바일에서 카드 세로 정렬", st.session_state.f_stack,
                                               disabled=st.session_state.f_approved,
                                               help="끄면 표(table) 구조로, 관리자 에디터 호환성이 가장 높습니다. "
                                                    "켜면 좁은 화면에서 카드가 자동으로 아래로 떨어집니다.")
        st.session_state.f_approved = st.checkbox("🔒 디자인 승인됨 (컬러·레이아웃 잠금)", st.session_state.f_approved,
                                                  help="승인된 디자인은 바뀌지 않도록 설정을 잠급니다. 문구 수정은 계속 가능합니다.")

        st.markdown('<div class="sec-hdr">💾 작업 저장 / 불러오기</div>', unsafe_allow_html=True)
        proj = {k: st.session_state[k] for k in ("f_title", "f_subtitle", "f_manuscript", "f_extra", "f_point",
                                                 "f_direction", "f_markup", "f_maxw", "f_stack", "f_approved")}
        st.download_button("작업 파일 저장 (.json)", json.dumps(proj, ensure_ascii=False, indent=1).encode("utf-8"),
                           file_name=f"강좌특징_{st.session_state.f_title or '작업'}.json", mime="application/json",
                           use_container_width=True)
        up = st.file_uploader("작업 파일 불러오기", type=["json"], key="f_proj_up", label_visibility="collapsed")
        if up is not None and st.session_state.get("_f_loaded") != up.name + str(up.size):
            try:
                data = json.loads(up.getvalue().decode("utf-8"))
                for k, v in data.items():
                    if k in _FEAT_DEFAULTS:
                        st.session_state[k] = v
                st.session_state["_f_loaded"] = up.name + str(up.size)
                st.session_state.pop("f_markup_area", None)
                st.rerun()
            except Exception as e:
                st.error(f"불러오기 실패: {e}")

    st.markdown("### 📝 강좌 특징 HTML 만들기")
    st.caption("원고를 넣으면 관리자 페이지 '강좌 특징' 영역에 바로 붙여넣을 HTML(.txt)과 디자인 미리보기(.html)를 만듭니다.")

    L, R = st.columns([1, 1.25], gap="large")
    with L:
        st.markdown("**① 원고 입력**")
        st.session_state.f_title = st.text_input("강좌명", st.session_state.f_title, placeholder="예: 2028 KISS LOGIC")
        st.session_state.f_subtitle = st.text_input("서브 타이틀", st.session_state.f_subtitle,
                                                    placeholder="예: 복잡한 구문을 걷어내는 수능 영어 독해 기본서")
        st.session_state.f_manuscript = st.text_area("강좌 소개 원고", st.session_state.f_manuscript, height=260,
                                                     placeholder="기존 이미지형 강좌 소개에 들어간 원고를 그대로 붙여넣으세요.")
        st.session_state.f_direction = st.text_input("디자인 방향 (선택)", st.session_state.f_direction,
                                                     placeholder="별도 요청 없으면 기본 네이비")
        st.session_state.f_extra = st.text_area("추가 요청사항 (선택)", st.session_state.f_extra, height=70,
                                                placeholder="예: 교재 라인업은 3단 박스로, 마지막에 수강 대상 정리")

        b1, b2 = st.columns(2)
        with b1:
            go_ai = st.button("✨ AI로 구조화", type="primary", use_container_width=True)
        with b2:
            go_plain = st.button("AI 없이 원고 그대로", use_container_width=True)
        if go_ai or go_plain:
            if not st.session_state.f_manuscript.strip():
                st.warning("원고를 먼저 입력해주세요.")
            elif go_plain:
                st.session_state.f_markup = feat_plain_markup(st.session_state.f_title, st.session_state.f_subtitle,
                                                              st.session_state.f_manuscript)
                st.session_state.f_changes = []
                st.session_state.pop("f_markup_area", None)   # 편집창 내용도 새 값으로 교체
                st.rerun()
            elif not st.session_state.api_key:
                st.warning("사이드바에 API 키를 입력해주세요.")
            else:
                with st.spinner("원고를 챕터·박스 구조로 정리하는 중..."):
                    try:
                        r = feat_ai_convert(st.session_state.f_title, st.session_state.f_subtitle,
                                            st.session_state.f_manuscript, st.session_state.f_direction,
                                            st.session_state.f_extra)
                        st.session_state.f_markup = r["markup"]
                        st.session_state.f_changes = r["changes"]
                        st.session_state.pop("f_markup_area", None)
                        st.rerun()
                    except Exception as e:
                        st.error(f"구조화 실패: {e}")

        if st.session_state.f_markup:
            st.markdown("**② 편집 마크업** — 여기서 직접 고치면 오른쪽 미리보기에 바로 반영됩니다")
            with st.expander("마크업 문법 보기", expanded=False):
                st.code(FEAT_MARKUP_GUIDE, language=None)
            st.session_state.f_markup = st.text_area("마크업", st.session_state.f_markup, height=420,
                                                     label_visibility="collapsed", key="f_markup_area")

            # 부분 수정
            st.markdown("**③ 부분 수정 요청** — 고른 부분만 바뀌고 나머지는 그대로 유지됩니다")
            head, chs = feat_split_chapters(st.session_state.f_markup)
            opts = ["머리 부분 (강좌명·서브타이틀·도입)"] + [f"{i + 1:02d}. {c.splitlines()[0][2:].strip()}" for i, c in enumerate(chs)]
            tgt = st.selectbox("수정할 부분", range(len(opts)), format_func=lambda i: opts[i], key="f_tgt")
            req = st.text_input("수정 요청", placeholder="예: 교재 3권을 3단 카드로 바꿔줘 / 두 번째 문단 오탈자만 확인",
                                key="f_req")
            if st.button("이 부분만 수정", use_container_width=True):
                if not req.strip():
                    st.warning("수정 요청을 입력해주세요.")
                elif not st.session_state.api_key:
                    st.warning("API 키가 필요합니다.")
                else:
                    with st.spinner("선택한 부분만 수정하는 중..."):
                        try:
                            st.session_state.f_markup = feat_ai_partial(st.session_state.f_markup, tgt - 1, req,
                                                                        st.session_state.f_manuscript)
                            st.session_state.pop("f_markup_area", None)
                            st.rerun()
                        except Exception as e:
                            st.error(f"수정 실패: {e}")

    with R:
        if not st.session_state.f_markup:
            st.info("왼쪽에 원고를 넣고 'AI로 구조화'를 누르면 여기에 미리보기가 나타납니다.")
            return
        doc = feat_parse(st.session_state.f_markup)
        fragment = feat_render(doc, st.session_state.f_point, st.session_state.f_maxw, st.session_state.f_stack)
        preview = feat_preview_html(fragment, doc.get("title") or st.session_state.f_title)
        name = re.sub(r'[\\/:*?"<>|\s]+', "_", doc.get("title") or st.session_state.f_title or "강좌")

        d1, d2 = st.columns(2)
        with d1:
            st.download_button("① 관리자 HTML 코드 (.txt)", fragment.encode("utf-8"),
                               file_name=f"{name}_강좌특징_관리자코드.txt", mime="text/plain; charset=utf-8",
                               type="primary", use_container_width=True)
        with d2:
            st.download_button("② 디자인 미리보기 (.html)", preview.encode("utf-8"),
                               file_name=f"{name}_강좌특징_미리보기.html", mime="text/html; charset=utf-8",
                               use_container_width=True)

        # 원고 대비 검사
        chk = feat_check("\n".join([st.session_state.f_manuscript, st.session_state.f_title,
                                     st.session_state.f_subtitle, st.session_state.f_extra]), st.session_state.f_markup)
        warns = []
        if chk["new_numbers"]:
            warns.append(f"원고에 없는 숫자: {', '.join(chk['new_numbers'][:8])}")
        if chk["hl_count"] > 3:
            warns.append(f"하이라이트 {chk['hl_count']}곳 (가이드: 2~3곳)")
        if chk["new_lines"]:
            warns.append(f"원고와 많이 다른 문장 {len(chk['new_lines'])}개")
        if chk["missing"]:
            warns.append(f"빠졌을 수 있는 원고 문장 {len(chk['missing'])}개")
        if warns:
            st.warning("검토 필요 · " + " / ".join(warns))
        else:
            st.success(f"원고 대비 검사 통과 · 하이라이트 {chk['hl_count']}곳 · 굵게 {chk['bold_count']}곳")
        with st.expander("검사 상세 · 교정 내역", expanded=bool(chk["new_lines"] or chk["missing"])):
            if chk["new_lines"]:
                st.markdown("**원고와 많이 다른 문장** (원고 일치율)")
                for t, p in chk["new_lines"]:
                    st.caption(f"· {t}  —  {p}%")
            if chk["missing"]:
                st.markdown("**결과에 잘 안 보이는 원고 문장**")
                for t in chk["missing"]:
                    st.caption(f"· {t}")
            if st.session_state.f_changes:
                st.markdown("**AI 교정 내역**")
                for ch in st.session_state.f_changes:
                    if isinstance(ch, dict):
                        st.caption(f"· {ch.get('before', '')} → {ch.get('after', '')}  ({ch.get('reason', '')})")
            if not (chk["new_lines"] or chk["missing"] or st.session_state.f_changes):
                st.caption("특이사항 없음")

        tab1, tab2 = st.tabs(["미리보기", "HTML 코드"])
        with tab1:
            vw = st.radio("화면", ["PC", "모바일"], horizontal=True, label_visibility="collapsed", key="f_vw")
            if hasattr(st, "iframe"):
                st.iframe(preview, height=900, width=390 if vw == "모바일" else "stretch")
            else:
                import streamlit.components.v1 as components
                components.html(preview, height=900, width=390 if vw == "모바일" else None, scrolling=True)
        with tab2:
            st.caption("오른쪽 위 복사 버튼으로 전체 복사 → 관리자 페이지 HTML 탭에 붙여넣기")
            st.code(fragment, language="html")


# ══════════════════════════════════════════════════════════════════════
# [v10] ✨ 시안형 PR 페이지 (에디토리얼 모드)
#
#  실제 대성마이맥 PR 시안(Deviser · The GUIDANCE · REAL CLOSING · CONTACT)의 문법을 코드로 옮긴 모드.
#   1) AI가 '컨셉 키트'(컨셉 단어·동사·「키워드」·대구)를 먼저 정하고
#   2) 블록 라이브러리에서 이번 강좌에 맞는 구성을 골라 문구를 채움 → 페이지마다 구성이 달라짐
#   3) 디자인은 스타일 팩(세리프 워드마크 + 단일 포인트 컬러)이 담당 → 매번 달라도 늘 정돈됨
#  가격·혜택·기간은 MD 입력값만 쓰고, AI는 숫자를 지어내지 않습니다.
# ══════════════════════════════════════════════════════════════════════
import html as _ehtml
import math
import random as _erandom

ED_PACKS = {
    # head: 한글 제목 서체 — sans(Pretendard 800) / serif(명조, 프리미엄·클래식 팩에서 큰 제목에만). 본문은 항상 Pretendard.
    "noir_navy":    {"name": "누아르 네이비 (Deviser형)",   "dark": "#0D0E11", "alt": "#EEF0F4", "accent": "#2C4A8C", "accent2": "#1E3570",
                     "en": "'Playfair Display'", "wm": "silver", "head": "serif"},
    "silver_mono":  {"name": "실버 모노 (GUIDANCE형)",      "dark": "#1B1B1C", "alt": "#F2F2F2", "accent": "#5E5E5E", "accent2": "#2B2B2B",
                     "en": "'Montserrat'", "wm": "fade", "head": "sans"},
    "dusty_rose":   {"name": "더스티 로즈 (CONTACT형)",     "dark": "#2F2E2F", "alt": "#F3EFEE", "accent": "#A57A80", "accent2": "#8A6066",
                     "en": "'Playfair Display'", "wm": "white", "head": "serif"},
    "blue_final":   {"name": "딥 블루 (REAL CLOSING형)",    "dark": "#0C1120", "alt": "#E8EDF6", "accent": "#2F5BEA", "accent2": "#1C3FB8",
                     "en": "'Space Grotesk'", "wm": "white", "head": "sans"},
    "ocean_mint":   {"name": "오션 민트 (입문·청량)",        "dark": "#06161C", "alt": "#E8F5F4", "accent": "#0E9AA7", "accent2": "#0B6E7A",
                     "en": "'Bebas Neue'", "wm": "white", "head": "sans"},
    "forest_ivory": {"name": "포레스트 아이보리",            "dark": "#13221C", "alt": "#F2F0E8", "accent": "#4E7A5C", "accent2": "#365A42",
                     "en": "'Montserrat'", "wm": "silver", "head": "sans"},
    "burgundy":     {"name": "버건디 클래식",                "dark": "#1A0E11", "alt": "#F5EEEF", "accent": "#8C2F42", "accent2": "#6C2232",
                     "en": "'Playfair Display'", "wm": "white", "head": "serif"},
}
ED_EN_FONTS = {"'Playfair Display'": "Playfair+Display:wght@500;600;700", "'Montserrat'": "Montserrat:wght@500;600;700;800",
               "'Space Grotesk'": "Space+Grotesk:wght@500;600;700", "'Bebas Neue'": "Bebas+Neue"}
ED_HERO_VARIANTS = {
    "wordmark_photo": "중앙 워드마크 + 강사 사진 (Deviser형)",
    "bottom_wordmark": "하단 대형 워드마크 + 풀사진 (GUIDANCE형)",
    "split_motif": "좌 모티프 / 우 워드마크 (CONTACT형)",
    "framed_spaced": "자간 넓은 타이틀 + 액자 사진 (REAL CLOSING형)",
    "fullbleed": "풀배경 이미지 + 중앙 워드마크",
    "light_editorial": "밝은 배경 + 좌 타이포 / 우 키비주얼",
}
ED_LAYOUT_BLOCKS = {"prologue": "가운데 정렬 / 이미지+텍스트 2단 / 풀배경 이미지",
                    "points": "지그재그 / 3열 키워드 카드 / 세로 타임라인",
                    "quote": "밝은 배경 / 어두운 배경 / 좌우 분할",
                    "three_col": "이미지 띠 / 카드형 / 지그재그 행",
                    "statement": "밝은 배경 / 어두운 배경"}
ED_COPIED_PHRASES = ["왜 첫 문장에서 손이 멈출까", "빈칸은 감이 아니라 근거", "주어부터 찾는 습관", "통합의 시대를 설계", "파이널은 밸런스 싸움", "허점은 닫고", "감각은 열고", "A distinct INSIGHT",
                     "A clear GUIDELINE", "완성도를 설계", "깊이감을 설계", "무엇을 알고, 어디까지 이해하고"]

ED_STYLE_GUIDE = """
[대성마이맥 PR 시안 문법 — 구조만 참고한다. 아래 '패턴'을 이 강좌 내용으로 새로 써야 하며, 다른 강좌의 문장을 가져오지 않는다]
A. 컨셉 동사 하나를 정해 섹션 '제목'에서만 변주한다. (예: 설계하다 → ~의 시대를 설계하다 / ~을 설계하다)
B. 영문 타이틀 + 한글 서술 한 줄의 짝. 영문은 강좌 내용과 직접 관련된 단어로, 페이지 안에서 같은 영문 패턴을 두 번 쓰지 않는다.
C. 대구는 페이지 전체에서 1번만. 두 구절이 모두 '이 강좌가 실제로 하는 일'이어야 한다. 말이 안 되는 대구(예: '해설은 멈춘다')는 쓰지 않는다.
D. 「키워드」 3개는 실제 학습 내용을 가리키는 짧은 말(예: 구문·적용·완독)로 정하고 기획 의도 포인트마다 하나씩 붙인다. 비유어(파도·보드 등)를 키워드로 쓰지 않는다.

[★ 메타포 사용 규칙 — AI 티가 나는 가장 큰 원인]
1. 컨셉 비유어(파도·보드·계단·설계도 같은 단어)는 히어로, 프롤로그 제목, 「키워드」, 마지막 한 줄에만 쓴다. 페이지 전체에서 5번 이하.
2. 설명(desc)·본문(body)·목록은 비유 없이 '실제로 무엇을 배우고 어떻게 공부하는지'를 평이하게 쓴다.
   ✗ "파도처럼 흐르는 구문 구조를 배웁니다" → ✓ "문장을 어디서 끊어 읽을지 기준을 세웁니다"
   ✗ "보드 위 균형처럼 정확히 적용한다" → ✓ "배운 구문을 실제 지문에서 찾아 해석합니다"
3. '~처럼 ~한다', 'A는 B, 우리는 C다' 같은 직유·은유 문장은 페이지 전체에서 1개 이하.

[자연스러움 규칙]
- 학생이 실제로 하는 말, 수업에서 실제로 하는 일로 쓴다. 광고 문구처럼 꾸미지 않는다.
- 지어낸 1인칭 수강생 고백("나는 ~가 필요했습니다")을 쓰지 않는다.
- 짧은 서술형 종결(~합니다, ~입니다)이 기본. 본문은 2~3문장 안쪽.
- 숫자·가격·기간·비율은 [강좌 정보]에 있는 것만. 없으면 그 블록을 쓰지 않는다.
- 쓰지 않는 표현: 체계적인, 최고의, 함께라면, ~와 함께하면, ~가 두렵지 않습니다, 해답을 찾으세요, 자신감을 얻는다, 비법, 여정, 첫걸음, 잠재력, 한계를 넘어, ~하는 당신, ~해드립니다.
- 히어로 아래 설명은 '이 강좌를 들으면 무엇이 달라지는지'를 학생의 실제 장면으로 쓴다. 광고 맺음말(함께하면 ~합니다)로 끝내지 않는다.
"""

ED_CRAFT_GUIDE = """
[세련된 카피 — 시니어 카피라이터가 실제로 고민하는 지점. 예시 문장은 그대로 쓰지 말 것]
1. 먼저 '이 강좌를 들을 학생이 속으로 하는 말'을 찾는다. 히어로·프롤로그는 그 말에서 출발한다.
   좋은 방향: 시험장에서 실제로 멈추는 순간을 짚는 질문 — 예) 단어는 다 아는데, 왜 첫 문장에서 손이 멈출까 (그대로 쓰지 말 것)
   컨셉 비유는 그 고민에 '답하는 쪽'에만 짧게 붙인다. 비유를 두 개 이상 겹치지 않는다(조각배·보드·파도를 한 문장에 함께 쓰는 식 ✗).
   (방향 예: "해석은 되는데 답이 안 보인다면" 처럼 학생이 실제로 겪는 상황)
2. 형용사 대신 구체적인 행동을 쓴다. '확실한 실력' ✗ → '처음 보는 지문에서도 주어와 동사부터 찾는다' ✓
3. 이 강좌에만 맞는 말인지 확인한다. 강좌명만 바꿔 다른 강좌에 붙여도 말이 되면 다시 쓴다.
4. 재정의(학생이 잘못 알고 있는 것을 바로잡는 문장)는 페이지 전체에서 1번. 'A가 아니라 B' 구조를 반복하지 않는다.
5. 리듬: 짧은 문장 다음에 조금 긴 문장. 제목은 10~22자. 명사로 끝나는 제목과 '~합니다'로 끝나는 설명을 섞는다.
   같은 어미(~다, ~는, ~까)로 끝나는 제목이 세 번 연달아 나오지 않게 한다.
6. 덜어내기: 같은 뜻이 두 번 나오면 하나를 지운다. 매우·정말·완벽한·확실한·제대로 같은 강조어는 쓰지 않는다.
7. 근거 없는 약속(반드시 오른다, 등급 보장)은 쓰지 않는다. 마지막 한 줄은 느낌표·명령형 대신 담백하게 끝낸다.
"""

ED_FULL_ORDER = ["hero", "prologue", "statement", "points", "quote", "three_col", "course_stages", "index_tiles",
                 "combo", "feature_stat", "balance", "manifesto", "target", "video", "lineup", "pass_box", "benefit"]

# 핵심 문구(후보를 여러 개 써 볼 가치가 있는 칸)와 그 역할
ED_KEY_FIELDS = {
    "hero": {"kicker": "히어로 워드마크 위 한 줄 (첫인상)", "sub": "히어로 한 줄 정의"},
    "prologue": {"title": "프롤로그 제목 (컨셉 명사구)", "sub": "프롤로그 부제", "closing": "프롤로그 마무리 한 줄"},
    "statement": {"line": "섹션 사이 큰 선언 문장", "sub": "선언을 받는 한 줄"},
    "quote": {"title": "기획 의도 질문형 제목", "closing": "기획 의도 마무리"},
    "three_col": {"title_ko": "특징 섹션 한글 제목"},
    "manifesto": {"kicker": "메시지 섹션 윗줄", "title": "메시지 섹션 선언형 제목", "closing": "메시지 마무리 한 줄"},
    "index_tiles": {"title": "라인업 제목"}, "combo": {"title": "구성 다이어그램 제목"},
    "feature_stat": {"title": "구성 수치 섹션 제목"}, "lineup": {"title_ko": "교재 섹션 한글 제목"},
    "video": {"title": "OT 영상 제목"},
    "target": {"title": "수강 대상 섹션 제목"},
}

# 편집 화면에 보이는 칸 이름 (영문 키 → 한글)
ED_FIELD_LABELS = {
    "kicker": "윗줄 문구", "sub": "부제 · 한 줄 설명", "title": "제목", "title_ko": "한글 제목", "title_en": "영문 제목",
    "closing": "마무리 한 줄", "line": "선언 문장", "body": "본문", "wordmark": "워드마크 (강좌명)", "script": "필기체 영단어",
    "notes": "사진 주변 짧은 문구", "band": "띠 문구", "lead": "첫 문장", "chapter": "챕터 라벨", "nav": "메뉴 이름",
    "eyebrow": "영문 윗줄", "points": "포인트 목록", "items": "항목 목록", "tiles": "타일 목록", "stages": "단계 목록",
    "label": "영문 라벨", "box": "강조 박스 문장", "stat": "핵심 수치", "tags": "태그", "caption": "설명 한 줄",
    "bridge": "연결 문장", "checks": "체크리스트", "features": "특징 목록", "books": "교재 목록", "structure": "구성 목록", "rows": "혜택 표",
    "pill": "영문 라벨", "conclusion": "결론", "left": "왼쪽 (A)", "right": "오른쪽 (B)", "no": "번호",
}

# 정보가 있어야 쓸 수 있는 섹션 — 어디에 무엇을 적으면 되는지
ED_NEEDS_HELP = {
    "feature_stat": "① 강좌 정보 › 기획 메모에 회차·문항 수를 적어주세요. 예: 총 20강 · 160문항 · 주 2회",
    "balance": "① 강좌 정보 › 기획 메모에 비율을 적어주세요. 예: 개념 40% · 실전 60%",
    "index_tiles": "① 강좌 정보 › 강좌 라인업 칸에 강좌명을 한 줄에 하나씩, 3개 이상 적어주세요.",
    "course_stages": "① 강좌 정보 › 강좌 라인업 칸에 강좌명과 단계를 적어주세요. 예: KEY STEP (기초)",
    "lineup": "① 강좌 정보 › 교재 정보 칸에 교재명·구성을 적거나, 사이드바에 교재 이미지를 올려주세요.",
    "video": "사이드바 › 🎬 OT 영상에 유튜브 링크를 넣어주세요.",
    "pass_box": "② 구매 · 혜택 › 상품명을 적어주세요.",
    "benefit": "② 구매 · 혜택 › 혜택·이벤트 칸을 채워주세요.",
}

ED_BLOCK_SPECS = {
    "hero": ('히어로(항상 첫 블록)',
             '{"type":"hero","variant":"wordmark_photo|bottom_wordmark|split_motif|framed_spaced|fullbleed|light_editorial","kicker":"워드마크 위/아래 한 줄 — 컨셉 동사 문장 (예: 통합의 시대를 설계하다)",'
             '"script":"워드마크 앞 필기체 영단어(선택, 예: The)","wordmark":"강좌명 영문 그대로","sub":"한 줄 정의 (20~34자)",'
             '"band":"사진 위 띠 문구 — 대구 (framed_spaced용, 예: 허점은 닫고, 감각은 열고)","notes":["사진 주변 짧은 문구 2~4개 (12~22자)"],'
             '"body":["히어로 하단 문장 2~3줄 (framed_spaced용)"]}'),
    "prologue": ('프롤로그 — 왜 이 강좌인가',
                 '{"type":"prologue","layout":"a|b|c","nav":"프롤로그","script":"Prologue","title":"컨셉 명사구 (예: 통합의 시대)","sub":"한 줄 (예: 새로운 수능, 새로운 설계의 필요성)",'
                 '"body":["문단 1 (40~80자)","문단 2 (40~80자)"],"closing":"마무리 선언 한 줄 — 컨셉 동사 포함"}'),
    "index_tiles": ('강좌 라인업 목차 타일 (강좌가 3개 이상일 때)',
                    '{"type":"index_tiles","nav":"라인업","eyebrow":"영문 (예: DEVISING The METHOD)","title":"컨셉 동사 제목, 핵심어 [[ ]]","sub":"한 줄",'
                    '"tiles":["강좌/교재명 — 입력 정보에 있는 것만"]}'),
    "course_stages": ('단계별 강좌 소개 (이론/훈련/실전 등)',
                      '{"type":"course_stages","nav":"커리큘럼","stages":[{"no":"01","label":"단계명 (예: 이론)","items":[{"badge":"1st Signature 등 (선택)","name":"강좌명(입력값)","title":"강좌 한 줄 정의","desc":"30~70자"}]}]}'),
    "points": ('기획 의도 포인트 3개 + 「키워드」 (지그재그)',
               '{"type":"points","layout":"a|b|c","nav":"기획 의도","title_en":"강좌명 영문","title_ko":"기획 의도","points":[{"label":"영문 라벨 (예: Contact Point 01)","desc":"설명 1~2문장 (30~60자)","keyword":"컨셉 「키워드」 단어 하나","line":"키워드가 들어가는 한 줄 (예: 추론형 실력 향상으로 향하는)"}]}'),
    "quote": ('기획 의도 인용형 (큰 따옴표 + 질문형 제목)',
              '{"type":"quote","layout":"a|b|c","nav":"기획 의도","chapter":"Chapter 01. 기획 의도","title":"질문형 대구 제목 (예: 무엇을 알고, 어디까지 이해하고, 어떻게 적용할 것인가)",'
              '"lead":"첫 줄 (첫 글자를 크게)","body":["문장 1","문장 2"],"closing":"굵게 마무리 1~2문장"}'),
    "three_col": ('영문 타이틀 + 3열 특징',
                  '{"type":"three_col","layout":"a|b|c","nav":"특징","chapter":"Chapter 02. 설계의 기준","title_en":"영문 (예: A distinct INSIGHT)","title_ko":"서술 한 줄 (예: 과목의 본질을 꿰뚫다)",'
                  '"items":[{"no":"01","small":"작은 설명 한 줄","title":"특징명 4~8자","desc":"20~50자"}]}'),
    "balance": ('A vs B 비율 바 (입력 정보에 비율이 있을 때만)',
                '{"type":"balance","nav":"밸런스","pill":"영문 라벨","title":"단언형 제목 (예: 파이널은 밸런스 싸움이다)","sub":"한 줄",'
                '"left":{"name":"A","sub":"설명","pct":"입력값"},"right":{"name":"B","sub":"설명","pct":"입력값"},'
                '"left_title":"A쪽 진단 한 줄","left_tags":["태그"],"right_title":"B쪽 진단 한 줄","right_tags":["태그"],"conclusion":"결론 1~2문장"}'),
    "combo": ('A + B 조합 다이어그램 (교재·유형 구성)',
              '{"type":"combo","nav":"구성","no":"01","title":"제목","left":{"tag":"A 이름","items":["항목"]},"right":{"tag":"B 이름","items":["항목"]},'
              '"left_result":"A 설명 한 줄","right_result":"B 설명 한 줄"}'),
    "feature_stat": ('핵심 구성 수치 + 특징 3개 (수치가 입력 정보에 있을 때)',
                     '{"type":"feature_stat","nav":"구성","no":"02","title":"제목","stat":"입력 수치 (예: 20 Sessions · 160 Questions)","tags":["태그"],"caption":"한 줄",'
                     '"bridge":"아래 특징으로 이어지는 한 줄","features":[{"title":"특징","desc":"설명 한 줄"}]}'),
    "manifesto": ('대구 선언 + 강조 박스 (강사 사진과 함께)',
                  '{"type":"manifesto","nav":"메시지","kicker":"대구 한 줄","title":"선언형 제목","box":"강조 박스 문장","body":["문장","문장"],"closing":"마무리 한 줄"}'),
    "statement": ('한 줄 선언 (섹션 사이 전환용, 큰 타이포)',
                  '{"type":"statement","layout":"a|b","line":"이 강좌의 핵심을 평이하게 말하는 한 문장 (18~32자)","sub":"그 문장을 받는 한 줄 (20~40자)"}'),
    "target": ('수강 대상 — 이런 학생에게 (체크리스트)',
               '{"type":"target","nav":"수강 대상","chapter":"Chapter 04. 수강 대상","title":"대상 학생을 부르는 제목 (예: 이런 학생이라면 지금 시작하세요 ✗ → 구체적인 상황으로)",'
               '"sub":"한 줄","checks":[{"title":"학생이 실제로 겪는 상황 한 줄 (15~30자)","desc":"이 강좌가 그 상황에서 해주는 일 (20~45자)"}],"closing":"(선택) 한 줄"}  — checks는 4개, [강좌 정보]의 대상·메모에 근거'),
    "video": ('OT 영상', '{"type":"video","nav":"OT","chapter":"Chapter 00. 오리엔테이션","title":"컨셉 명사구 (예: 설계자의 가이드)","label":"영문 (예: Orientation)"}'),
    "lineup": ('교재 라인업·구성 (교재 정보가 있을 때)',
               '{"type":"lineup","nav":"교재","chapter":"Chapter 03. 교재 구성","title_en":"영문 (예: A clear GUIDELINE)","title_ko":"서술 한 줄",'
               '"books":[{"name":"교재명(입력값)","items":["구성(입력값)"]}],"structure":[{"no":"01","name":"섹션명","desc":"설명"}]}'),
    "pass_box": ('구매 박스 (가격은 MD 입력값을 코드가 채움)', '{"type":"pass_box","nav":"구매하기","title":"구매 섹션 제목 (예: 2028 Deviser 교재패스)"}'),
    "benefit": ('혜택 안내 (혜택 정보가 있을 때)', '{"type":"benefit","nav":"혜택","title":"혜택 제목","rows":[["항목","입력값"]]}'),
}

def _ed_esc(s) -> str:
    s = strip_hanja(str(s or ""))
    s = _ehtml.escape(s, quote=False)
    s = re.sub(r"\[\[(.+?)\]\]", r'<span class="ed-acc">\1</span>', s)
    s = re.sub(r"「(.+?)」", r'<span class="ed-acc">「\1」</span>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return s.replace("\n", "<br>")

def _ed_spaced(s: str) -> str:
    """한 글자씩 띄운 타이틀 (Deviser 하단 '통 합 의 시 대 를 …' 느낌)"""
    return " ".join(list(strip_hanja(str(s or "")).replace(" ", " ")))


# ── 블록 렌더러 ───────────────────────────────────────────
def _ed_head(chapter="", title="", sub="", en=False, dark=False) -> str:
    return ('<div class="ed-head">'
            + (f'<span class="ed-pill">{_ed_esc(chapter)}</span>' if chapter else "")
            + (f'<h2 class="ed-h{" ed-en" if en else ""}">{_ed_esc(title)}</h2>' if title else "")
            + (f'<p class="ed-hsub">{_ed_esc(sub)}</p>' if sub else "")
            + '<div class="ed-rule"></div></div>')

def _ed_motif_kind(motif: str) -> str:
    m = motif or ""
    if re.search(r"계단|단계|디딤|step|stair", m, re.I): return "stairs"
    if re.search(r"파도|물결|서핑|surf|wave|바다|흐름", m, re.I): return "waves"
    if re.search(r"설계|도면|청사진|blueprint|devis|구조|격자|grid", m, re.I): return "blueprint"
    if re.search(r"빛|광|light|ray|별|star|태양|sun", m, re.I): return "rays"
    return "arcs"

def _ed_motif_svg(color: str, motif: str = "", w: str = "100%", maxw: int = 420, op: float = 1.0) -> str:
    """컨셉 모티프 SVG — 계단 / 파도 / 설계도 / 빛줄기 / 동심 원호(기본)"""
    kind = _ed_motif_kind(motif)
    g = ""
    if kind == "stairs":
        for i in range(8):
            x0, y0 = 40 + i * 48, 420 - i * 46
            o = 0.18 + i * 0.1
            g += (f'<path d="M{x0} {y0} H{x0 + 48} V{y0 - 46}" fill="none" stroke="{color}" stroke-opacity="{min(o,1):.2f}" stroke-width="2"/>'
                  f'<path d="M{x0} {y0 + 14} H{x0 + 48} V{y0 - 32}" fill="none" stroke="{color}" stroke-opacity="{min(o,1) * .35:.2f}" stroke-width="1"/>')
        g += f'<circle cx="424" cy="52" r="7" fill="{color}"/>'
    elif kind == "waves":
        for i in range(12):
            y = 120 + i * 22; amp = 18 + i * 2.2; ph = i * 14
            g += (f'<path d="M0 {y} C {60+ph} {y-amp}, {150+ph} {y+amp}, {230} {y} S {400-ph} {y-amp}, 460 {y}" fill="none" '
                  f'stroke="{color}" stroke-opacity="{0.12 + i * 0.06:.2f}" stroke-width="{1 + (i % 3) * .4:.1f}"/>')
    elif kind == "blueprint":
        for k in range(0, 461, 23):
            g += (f'<line x1="{k}" y1="0" x2="{k}" y2="460" stroke="{color}" stroke-opacity="{.22 if k % 115 == 0 else .07}" stroke-width="1"/>'
                  f'<line x1="0" y1="{k}" x2="460" y2="{k}" stroke="{color}" stroke-opacity="{.22 if k % 115 == 0 else .07}" stroke-width="1"/>')
        g += (f'<circle cx="230" cy="230" r="150" fill="none" stroke="{color}" stroke-opacity=".6" stroke-width="1.4"/>'
              f'<circle cx="230" cy="230" r="90" fill="none" stroke="{color}" stroke-opacity=".35" stroke-dasharray="6 6"/>'
              f'<line x1="40" y1="420" x2="420" y2="40" stroke="{color}" stroke-opacity=".5"/>')
    elif kind == "rays":
        for k in range(28):
            a = math.radians(k * (180 / 27))
            g += (f'<line x1="230" y1="430" x2="{230 + 420 * math.cos(a):.1f}" y2="{430 - 420 * math.sin(a):.1f}" '
                  f'stroke="{color}" stroke-opacity="{.08 + (k % 4) * .06:.2f}" stroke-width="1"/>')
        g += f'<circle cx="230" cy="430" r="40" fill="{color}" fill-opacity=".25"/>'
    else:
        g = "".join(f'<circle cx="230" cy="230" r="{120 + i * 7}" fill="none" stroke="{color}" stroke-opacity="{0.15 + i * 0.035:.2f}" stroke-width="1.2" '
                    f'stroke-dasharray="{560 + i * 30} 2000" transform="rotate({40 + i * 3} 230 230)"/>' for i in range(16))
    return f'<svg viewBox="0 0 460 460" width="{w}" style="max-width:{maxw}px;opacity:{op}" aria-hidden="true">{g}</svg>'

def _ed_deco_motif(x, pos: str = "br", color: str = "var(--accent)", op: float = .5, size: int = 520) -> str:
    """섹션 안 장식: 모티프 SVG를 모서리에 은은하게"""
    if not x.get("deco", True):
        return ""
    p = {"br": "right:-60px;bottom:-60px", "bl": "left:-60px;bottom:-60px", "tr": "right:-60px;top:-40px", "tl": "left:-60px;top:-40px"}[pos]
    return f'<div class="ed-deco" style="{p};width:{size}px">{_ed_motif_svg(color, x.get("motif", ""), "100%", size, op)}</div>'

def _ed_deco_word(x, word: str = "", pos: str = "tr", dark: bool = False) -> str:
    """섹션 안 장식: 아웃라인 대형 영문 (컨셉 단어)"""
    if not x.get("deco", True):
        return ""
    w = strip_hanja(word or x.get("concept_en") or "").upper()[:12]
    if not w:
        return ""
    p = {"tr": "right:-10px;top:30px", "tl": "left:-10px;top:30px", "br": "right:-10px;bottom:10px", "bl": "left:-10px;bottom:10px"}[pos]
    return f'<div class="ed-deco-word{" on-dark" if dark else ""}" style="{p}">{_ehtml.escape(w)}</div>'

def _ed_img(x, slot):
    return (x.get("imgs") or {}).get(slot) or ""

def ed_r_hero(b, x):
    v = b.get("variant") or "wordmark_photo"
    wm, kicker, sub, script = b.get("wordmark") or x["label"], b.get("kicker", ""), b.get("sub", ""), b.get("script", "")
    photo, book = x.get("photo"), (x.get("books") or [None])[0]
    hero_bg, kv = _ed_img(x, "hero_bg"), _ed_img(x, "key_visual")
    notes = [n for n in (b.get("notes") or []) if str(n).strip()][:4]
    n = len(strip_hanja(wm))
    wm_size = "clamp(64px,11vw,150px)" if n <= 9 else "clamp(52px,8vw,112px)" if n <= 16 else "clamp(40px,6vw,80px)"
    bg_layer = (f"linear-gradient(180deg,rgba(0,0,0,.35),rgba(0,0,0,.15) 40%,rgba(0,0,0,.75)),url('{hero_bg}') center/cover no-repeat," if hero_bg else "")

    if v == "fullbleed":
        bg = f"background:{bg_layer}radial-gradient(60% 60% at 50% 40%,color-mix(in srgb,var(--accent) 30%,transparent),transparent 70%),var(--dark);"
        nts = "".join(f"<span>{_ed_esc(t)}</span>" for t in notes[:3])
        return (f'<section class="ed-hero ed-dark" style="{bg}min-height:min(92vh,880px);display:flex;align-items:center;text-align:center">'
                f'<div class="ed-in" style="width:100%">'
                f'<p class="ed-spaced" style="margin-bottom:26px">{_ed_esc(_ed_spaced(kicker))}</p>'
                + (f'<div class="ed-script" style="font-size:clamp(48px,6vw,84px);color:#fff;line-height:1;margin-bottom:-.2em">{_ed_esc(script)}</div>' if script else "")
                + f'<h1 class="ed-wm ed-wm-silver" style="font-size:{wm_size}">{_ed_esc(wm)}</h1>'
                + (f'<p class="ed-sub-l" style="font-size:clamp(16px,1.6vw,20px);margin-top:22px">{_ed_esc(sub)}</p>' if sub else "")
                + (f'<div class="ed-hero-notes">{nts}</div>' if nts else "")
                + '</div></section>')

    if v == "light_editorial":
        right = (f'<img src="{book or kv}" alt="" style="max-width:100%;max-height:460px;filter:drop-shadow(0 30px 40px rgba(0,0,0,.25))">'
                 if (book or kv) else _ed_motif_svg("var(--accent)", x.get("motif", "")))
        return (f'<section class="ed-hero" style="background:var(--alt);min-height:min(82vh,760px);display:flex;align-items:center">'
                f'<div class="ed-in ed-split" style="width:100%;grid-template-columns:1.2fr 1fr"><div>'
                + (f'<p class="ed-serif" style="font-size:clamp(17px,1.7vw,22px);color:var(--muted);margin:0 0 10px">{_ed_esc(kicker)}</p>' if kicker else "")
                + (f'<div class="ed-script" style="font-size:clamp(40px,5vw,70px);color:var(--accent);line-height:1;margin-bottom:-.15em">{_ed_esc(script)}</div>' if script else "")
                + f'<h1 class="ed-wm" style="font-size:{wm_size};color:var(--accent2)">{_ed_esc(wm)}</h1>'
                + (f'<p class="ed-serif" style="font-size:clamp(18px,1.9vw,24px);color:var(--ink);margin:24px 0 0;line-height:1.5">{_ed_esc(sub)}</p>' if sub else "")
                + '<div style="width:64px;height:2px;background:var(--accent);margin-top:28px"></div>'
                + f'</div><div style="text-align:center">{right}</div></div></section>')

    if v == "bottom_wordmark":
        if photo:
            bg = f"background:linear-gradient(90deg,var(--dark) 18%,rgba(0,0,0,.25) 60%,rgba(0,0,0,.55)),url('{photo}') right center/auto 100% no-repeat,var(--dark);"
        elif hero_bg:
            bg = f"background:linear-gradient(180deg,rgba(0,0,0,.25),rgba(0,0,0,.55)),url('{hero_bg}') center/cover no-repeat,var(--dark);"
        else:
            bg = "background:radial-gradient(60% 70% at 70% 30%,rgba(255,255,255,.10),transparent 70%),var(--dark);"
        corners = (notes + ["", "", "", ""])[:4]
        return (f'<section class="ed-hero ed-dark" style="{bg}min-height:min(88vh,820px);padding:0">'
                f'<div class="ed-corner tl">{_ed_esc(corners[0])}</div><div class="ed-corner tr">{_ed_esc(corners[1])}</div>'
                f'<div class="ed-corner ml">{_ed_esc(corners[2])}</div><div class="ed-corner mr">{_ed_esc(corners[3])}</div>'
                f'<p class="ed-spaced" style="position:absolute;top:70px;left:0;right:0;text-align:center">{_ed_esc(kicker)}</p>'
                f'<div style="position:absolute;left:0;right:0;bottom:-0.12em;text-align:center">'
                + (f'<div class="ed-script" style="font-size:clamp(56px,8vw,110px);color:#fff;line-height:1;margin-bottom:-.25em">{_ed_esc(script)}</div>' if script else "")
                + f'<h1 class="ed-wm ed-wm-fade" style="font-size:clamp(80px,15vw,210px);line-height:.9">{_ed_esc(wm)}</h1></div></section>')

    if v == "split_motif":
        vis = book or kv
        left = (f'<img src="{vis}" alt="" style="max-width:100%;max-height:440px;filter:drop-shadow(0 30px 40px rgba(0,0,0,.5))">' if vis
                else _ed_motif_svg("#ffffff", x.get("motif", "")))
        bg = f"background:{bg_layer}var(--dark);" if hero_bg else ""
        return (f'<section class="ed-hero ed-dark" style="{bg}min-height:min(80vh,720px)"><div class="ed-in ed-split">'
                f'<div style="text-align:center">{left}</div><div style="text-align:right">'
                + (f'<p class="ed-serif" style="font-size:clamp(18px,1.8vw,24px);color:var(--muted);margin:0 0 6px">{_ed_esc(kicker)}</p>' if kicker else "")
                + (f'<p class="ed-serif" style="font-size:clamp(26px,3vw,40px);color:var(--accent-light);margin:0 0 4px">{_ed_esc(sub)}</p>' if sub else "")
                + f'<h1 class="ed-wm ed-wm-white" style="font-size:{wm_size}">{_ed_esc(wm)}</h1></div></div></section>')

    if v == "framed_spaced":
        words = strip_hanja(wm).split()
        first = _ed_spaced(words[0]) if len(words) > 1 else ""
        rest = " ".join(words[1:]) if len(words) > 1 else wm
        fimg = photo or hero_bg or kv
        frame = (f'<div class="ed-frame" style="background:url(\'{fimg}\') center 30%/cover no-repeat">' if fimg
                 else '<div class="ed-frame" style="background:linear-gradient(135deg,#3a3f4f,#151824)">')
        body = "".join(f"<p>{_ed_esc(t)}</p>" for t in (b.get("body") or []))
        return (f'<section class="ed-hero ed-dark" style="text-align:center;padding-top:80px"><div class="ed-in" style="max-width:880px">'
                f'<p class="ed-spaced" style="margin:0 0 22px">{_ed_esc(kicker)}</p>{frame}'
                + (f'<div class="ed-band">{_ed_esc(_ed_spaced(b.get("band","")))}</div>' if b.get("band") else "")
                + f'</div><div style="margin-top:-60px;position:relative">'
                + (f'<div class="ed-wm ed-wm-white" style="font-size:clamp(48px,8vw,104px);letter-spacing:.35em;margin-right:-.35em">{_ed_esc(first)}</div>' if first else "")
                + f'<h1 class="ed-wm ed-wm-white" style="font-size:clamp(48px,8vw,104px);margin-top:4px">{_ed_esc(rest)}</h1></div>'
                + (f'<p class="ed-sub-l" style="margin-top:30px">{_ed_esc(sub)}</p>' if sub else "")
                + (f'<div class="ed-herobody">{body}</div>' if body else "")
                + '</div></section>')

    # wordmark_photo (기본)
    if photo:
        ph = (f'<img src="{photo}" alt="" style="width:min(520px,80%);display:block;margin:-30px auto 0;filter:grayscale(1) contrast(1.05);'
              f'-webkit-mask-image:linear-gradient(180deg,#000 70%,transparent);mask-image:linear-gradient(180deg,#000 70%,transparent)">')
    elif kv and not hero_bg:
        ph = f'<img src="{kv}" alt="" style="width:min(420px,70%);display:block;margin:10px auto 0">'
    else:
        ph = '<div style="height:240px"></div>'
    ln = "".join(f'<p class="ed-note" style="top:{38 + i * 22}%">{_ed_esc(t)}</p>' for i, t in enumerate(notes[0::2]))
    rn = "".join(f'<p class="ed-note r" style="top:{44 + i * 22}%">{_ed_esc(t)}</p>' for i, t in enumerate(notes[1::2]))
    bg = f"background:{bg_layer}var(--dark);" if hero_bg else ""
    return (f'<section class="ed-hero ed-dark" style="{bg}text-align:center;padding:90px 24px 0;overflow:hidden">'
            f'<div class="ed-in" style="position:relative">'
            f'<h1 class="ed-wm ed-wm-silver" style="font-size:{wm_size};position:relative;z-index:2">{_ed_esc(wm)}</h1>'
            f'<p class="ed-spaced" style="position:relative;z-index:2;margin-top:6px">{_ed_esc(_ed_spaced(kicker))}</p>'
            + (f'<p class="ed-sub-l" style="position:relative;z-index:2">{_ed_esc(sub)}</p>' if sub else "")
            + f'{ln}{rn}{ph}</div></section>')

def ed_r_anchor_bar(navs):
    if not navs:
        return ""
    links = "".join(f'<a href="#{i}">{_ed_esc(l)}</a>' for i, l in navs)
    return f'<nav class="ed-anchor">{links}</nav>'

def ed_r_prologue(b, x):
    body = "".join(f"<p>{_ed_esc(t)}</p>" for t in (b.get("body") or []))
    img = _ed_img(x, "key_visual") or _ed_img(x, "texture")
    lay = b.get("layout") or "a"
    head = (f'<div class="ed-script" style="font-size:34px;color:var(--accent);margin-bottom:-6px">{_ed_esc(b.get("script") or "Prologue")}</div>'
            f'<h2 class="ed-h" style="font-size:clamp(34px,4.4vw,56px);color:{"#fff" if lay == "c" else "var(--accent2)"}">{_ed_esc(b.get("title",""))}</h2>'
            f'<p class="ed-hsub">{_ed_esc(b.get("sub",""))}</p>')
    closing = f'<p class="ed-closing">{_ed_esc(b.get("closing"))}</p>' if b.get("closing") else ""
    if lay == "b":
        vis = (f'<div class="ed-prolog-img" style="background:url(\'{img}\') center/cover no-repeat"></div>' if img
               else f'<div class="ed-prolog-img" style="background:var(--dark);display:flex;align-items:center;justify-content:center">{_ed_motif_svg("#ffffff", x.get("motif",""))}</div>')
        return (f'<section class="ed-sec ed-alt ed-ov">{_ed_deco_word(x, pos="br")}<div class="ed-in ed-split" style="grid-template-columns:1fr 1.15fr;align-items:center">'
                f'{vis}<div style="text-align:left">{head}<div class="ed-body" style="margin-top:34px;text-align:left">{body}</div>'
                f'<div style="text-align:left">{closing}</div></div></div></section>')
    if lay == "c":
        bgimg = _ed_img(x, "texture") or _ed_img(x, "hero_bg")
        bg = (f"background:linear-gradient(180deg,rgba(0,0,0,.78),rgba(0,0,0,.88)),url('{bgimg}') center/cover no-repeat,var(--dark)" if bgimg
              else "background:var(--dark)")
        return (f'<section class="ed-sec ed-dark ed-ov" style="{bg};text-align:center;padding:150px 24px">{_ed_deco_word(x, pos="tl", dark=True)}'
                f'{_ed_deco_motif(x, "br", "#ffffff", .25)}<div class="ed-in" style="max-width:760px">'
                f'{head}<div class="ed-body" style="margin-top:44px">{body}</div>{closing}</div></section>')
    return (f'<section class="ed-sec ed-alt ed-ov" style="text-align:center">{_ed_deco_word(x, pos="tr")}<div class="ed-in" style="max-width:760px">'
            f'{head}<div class="ed-body" style="margin-top:44px">{body}</div>{closing}</div></section>')

def ed_r_index_tiles(b, x):
    tiles = [t for t in (b.get("tiles") or []) if str(t).strip()]
    tex = _ed_img(x, "texture")
    cells = "".join(
        f'<div class="ed-tile"' + (f' style="background:linear-gradient(180deg,rgba(0,0,0,.25),rgba(0,0,0,.75)),url(\'{tex}\') {int(i * 100 / max(len(tiles) - 1, 1))}% center/auto 100% no-repeat"' if tex else "")
        + f'><span>{i + 1:02d}</span><b>{_ed_esc(t)}</b></div>' for i, t in enumerate(tiles))
    return (f'<section class="ed-sec ed-dark"><div class="ed-in" style="text-align:center">'
            f'<p class="ed-eyebrow">{_ed_esc(b.get("eyebrow",""))}</p>'
            f'<h2 class="ed-h" style="color:#fff">{_ed_esc(b.get("title",""))}</h2><p class="ed-hsub">{_ed_esc(b.get("sub",""))}</p>'
            f'<div class="ed-tiles" style="grid-template-columns:repeat({min(max(len(tiles),1),7)},1fr)">{cells}</div></div></section>')

def ed_r_course_stages(b, x):
    out = ""
    for st_ in b.get("stages") or []:
        items = ""
        for it in st_.get("items") or []:
            items += ('<div class="ed-course">'
                      f'<div class="ed-course-l">'
                      + (f'<span class="ed-script" style="font-size:20px;color:var(--accent)">{_ed_esc(it.get("badge"))}</span><br>' if it.get("badge") else "")
                      + f'<b class="ed-serif-en">{_ed_esc(it.get("name",""))}</b></div>'
                      f'<div class="ed-course-r"><h4>{_ed_esc(it.get("title",""))}</h4><p>{_ed_esc(it.get("desc",""))}</p></div></div>')
        out += (f'<div class="ed-stage"><div class="ed-stage-h"><span>{_ed_esc(st_.get("no",""))}</span> {_ed_esc(st_.get("label",""))}</div>{items}</div>')
    return f'<section class="ed-sec ed-dark" style="padding-top:40px"><div class="ed-in ed-boxline">{out}</div></section>'

def ed_r_points(b, x):
    pts = b.get("points") or []
    lay = b.get("layout") or "a"
    title = (f'<h2 class="ed-h" style="text-align:center;font-size:clamp(34px,4.6vw,58px)"><span class="ed-serif-en ed-acc2">'
             f'{_ed_esc(b.get("title_en",""))}</span> {_ed_esc(b.get("title_ko",""))}</h2>')
    if lay == "b":
        cards = "".join(
            f'<div class="ed-pcard"><span class="ed-serif-en ed-plabel">{_ed_esc(p.get("label",""))}</span>'
            f'<div class="ed-pkw">「{_ed_esc(p.get("keyword",""))}」</div>'
            f'<p class="ed-pline" style="font-size:17px">{_ed_esc(p.get("line",""))}</p>'
            f'<p class="ed-pdesc" style="margin-top:10px">{_ed_esc(p.get("desc",""))}</p></div>' for p in pts)
        return (f'<section class="ed-sec ed-alt ed-ov">{_ed_deco_motif(x, "tr", "var(--accent)", .35, 460)}<div class="ed-in">{title}'
                f'<div class="ed-pcards" style="grid-template-columns:repeat({max(min(len(pts),3),1)},1fr)">{cards}</div></div></section>')
    if lay == "c":
        rows = "".join(
            f'<div class="ed-tl-row"><div class="ed-tl-no">{i + 1:02d}</div><div class="ed-tl-body">'
            f'<span class="ed-serif-en ed-plabel">{_ed_esc(p.get("label",""))}</span>'
            f'<div class="ed-pkw" style="margin:6px 0 8px">「{_ed_esc(p.get("keyword",""))}」<small>{_ed_esc(p.get("line",""))}</small></div>'
            f'<p class="ed-pdesc">{_ed_esc(p.get("desc",""))}</p></div></div>' for i, p in enumerate(pts))
        return (f'<section class="ed-sec ed-ov">{_ed_deco_word(x, pos="tr")}<div class="ed-in" style="max-width:880px">{title}'
                f'<div class="ed-tl">{rows}</div></div></section>')
    rows = ""
    for i, p in enumerate(pts):
        side = "l" if i % 2 == 0 else "r"
        kw = p.get("keyword", "")
        rows += (f'<div class="ed-point {side}"><div class="ed-orb"></div><div class="ed-point-t">'
                 f'<span class="ed-serif-en ed-plabel">{_ed_esc(p.get("label",""))}</span>'
                 f'<p class="ed-pdesc">{_ed_esc(p.get("desc",""))}</p>'
                 f'<p class="ed-pline">{_ed_esc(p.get("line",""))}' + (f' <span class="ed-acc">「{_ed_esc(kw)}」</span>' if kw else "") + '</p>'
                 '</div></div>')
    return f'<section class="ed-sec ed-alt ed-diag ed-ov"><div class="ed-in">{title}<div class="ed-points">{rows}</div></div></section>'

def ed_r_quote(b, x):
    lead = strip_hanja(str(b.get("lead", "")))
    lay = b.get("layout") or "a"
    body_items = [t for t in (b.get("body") or []) if str(t).strip()]
    if lay == "c":
        lis = "".join(f'<li><span class="ed-ck"></span>{_ed_esc(t)}</li>' for t in body_items)
        return (f'<section class="ed-sec ed-ov">{_ed_deco_motif(x, "bl", "var(--accent)", .22, 380)}'
                f'<div class="ed-in ed-split" style="grid-template-columns:1fr 1.1fr;align-items:center">'
                f'<div><span class="ed-pill">{_ed_esc(b.get("chapter",""))}</span>'
                f'<h2 class="ed-h" style="font-weight:600">{_ed_esc(b.get("title",""))}</h2>'
                f'<p class="ed-serif ed-acc" style="font-size:clamp(20px,2.2vw,28px);margin:22px 0 0;line-height:1.5">{_ed_esc(lead)}</p></div>'
                f'<div><ul class="ed-cklist">{lis}</ul>'
                + (f'<p class="ed-closing" style="text-align:left;font-size:17px">{_ed_esc(b.get("closing"))}</p>' if b.get("closing") else "")
                + '</div></div></section>')
    lead_html = (f'<span style="font-size:1.6em;font-weight:700">{_ed_esc(lead[:1])}</span>{_ed_esc(lead[1:])}' if lead else "")
    body = "".join(f"<p>{_ed_esc(t)}</p>" for t in body_items)
    dark = lay == "b"
    tex = _ed_img(x, "texture") if dark else ""
    sec_style = (f"text-align:center;background:linear-gradient(180deg,rgba(0,0,0,.72),rgba(0,0,0,.86)),url('{tex}') center/cover no-repeat,var(--dark)" if tex
                 else "text-align:center")
    return (f'<section class="ed-sec{" ed-dark" if dark else ""} ed-ov" style="{sec_style}">'
            + (_ed_deco_motif(x, "br", "#ffffff", .18, 480) if dark else "")
            + '<div class="ed-in" style="max-width:820px">'
            + _ed_head(b.get("chapter", ""), b.get("title", ""))
            + f'<div class="ed-quote"><span class="q l">&ldquo;</span><span class="q r">&rdquo;</span>'
            f'<p class="ed-serif" style="font-size:20px;margin:0 0 16px">{lead_html}</p><div class="ed-body">{body}</div>'
            + (f'<p class="ed-closing" style="font-size:17px">{_ed_esc(b.get("closing"))}</p>' if b.get("closing") else "")
            + '</div></div></section>')

def ed_r_three_col(b, x):
    items_ = b.get("items") or []
    tex = _ed_img(x, "texture")
    lay = b.get("layout") or "a"
    head = (f'<span class="ed-pill">{_ed_esc(b.get("chapter",""))}</span>'
            f'<h2 class="ed-h ed-en" style="font-size:clamp(32px,4vw,50px)">{_ed_esc(b.get("title_en",""))}</h2>'
            f'<p class="ed-hsub ed-serif" style="font-size:20px">{_ed_esc(b.get("title_ko",""))}</p><div class="ed-rule"></div>')
    if lay == "c":
        rows = ""
        for i, it in enumerate(items_):
            pos = int(i * 100 / max(len(items_) - 1, 1))
            vis = (f'<div class="ed-zz-img" style="background:url(\'{tex}\') {pos}% center/cover no-repeat"></div>' if tex else
                   f'<div class="ed-zz-img" style="background:var(--dark);display:flex;align-items:center;justify-content:center">'
                   f'{_ed_motif_svg("#ffffff", x.get("motif",""), "70%", 260, .8)}</div>')
            txt = (f'<div class="ed-zz-t"><span class="ed-bignum2">{_ed_esc(it.get("no") or f"{i+1:02d}")}</span>'
                   f'<small>{_ed_esc(it.get("small",""))}</small><h4>{_ed_esc(it.get("title",""))}</h4><p>{_ed_esc(it.get("desc",""))}</p></div>')
            rows += f'<div class="ed-zz{" rev" if i % 2 else ""}">{vis}{txt}</div>'
        return (f'<section class="ed-sec ed-ov" style="text-align:center">{_ed_deco_word(x, pos="tl")}<div class="ed-in">{head}'
                f'<div class="ed-zzs">{rows}</div></div></section>')
    cards = lay == "b"
    out = ""
    for i, it in enumerate(items_):
        pos = int(i * 100 / max(len(items_) - 1, 1))
        bar = (f'<div class="ed-colbar ed-colimg" style="background:url(\'{tex}\') {pos}% center/auto 100% no-repeat"></div>' if tex
               else '<div class="ed-colbar"></div>')
        num = _ed_esc(it.get("no") or f"{i+1:02d}")
        if cards:
            out += (f'<div class="ed-col ed-colcard"><span class="ed-bignum2">{num}</span>'
                    f'<small>{_ed_esc(it.get("small",""))}</small><h4>{_ed_esc(it.get("title",""))}</h4>'
                    f'<p>{_ed_esc(it.get("desc",""))}</p></div>')
        else:
            out += (f'<div class="ed-col"><span class="ed-num">{num}</span>'
                    f'<small>{_ed_esc(it.get("small",""))}</small><h4>{_ed_esc(it.get("title",""))}</h4>'
                    f'{bar}<p>{_ed_esc(it.get("desc",""))}</p></div>')
    return (f'<section class="ed-sec{" ed-alt" if cards else ""} ed-ov" style="text-align:center">'
            + (_ed_deco_motif(x, "br", "var(--accent)", .25, 420) if cards else "")
            + f'<div class="ed-in">{head}<div class="ed-cols">{out}</div></div></section>')

def ed_r_statement(b, x):
    dark = (b.get("layout") or "a") == "b"
    return (f'<section class="ed-sec ed-ov{" ed-dark" if dark else ""}" style="text-align:center;padding:130px 24px">'
            f'{_ed_deco_motif(x, "bl", "#ffffff" if dark else "var(--accent)", .3 if dark else .4, 560)}'
            f'{_ed_deco_motif(x, "tr", "#ffffff" if dark else "var(--accent)", .15 if dark else .2, 360)}'
            f'<div class="ed-in" style="max-width:860px"><div class="ed-stline"></div>'
            f'<h2 class="ed-h" style="font-size:clamp(28px,3.8vw,48px);font-weight:600;line-height:1.45">{_ed_esc(b.get("line",""))}</h2>'
            + (f'<p class="ed-hsub" style="font-size:18px;margin-top:20px">{_ed_esc(b.get("sub"))}</p>' if b.get("sub") else "")
            + '</div></section>')

def ed_r_balance(b, x):
    L, R = b.get("left") or {}, b.get("right") or {}
    def _pct(v):
        m = re.search(r"\d{1,3}", str(v or ""))
        return int(m.group(0)) if m else None
    lp, rp = _pct(L.get("pct")), _pct(R.get("pct"))
    if lp is None and rp is None:
        lp, rp = 50, 50
    lp = lp if lp is not None else 100 - rp
    rp = rp if rp is not None else 100 - lp
    def tags(ts, cls):
        return "".join(f'<span class="ed-bubble {cls}">{_ed_esc(t)}</span>' for t in (ts or []))
    show_pct = _pct(L.get("pct")) is not None
    return (f'<section class="ed-sec ed-alt" style="text-align:center;padding-bottom:0"><div class="ed-in" style="max-width:820px">'
            f'<span class="ed-pillfill">{_ed_esc(b.get("pill",""))}</span>'
            f'<h2 class="ed-h" style="font-weight:700">{_ed_esc(b.get("title",""))}</h2><p class="ed-hsub">{_ed_esc(b.get("sub",""))}</p>'
            f'<div class="ed-barlabels"><div><b class="ed-serif-en">{_ed_esc(L.get("name",""))}</b><small>{_ed_esc(L.get("sub",""))}</small></div>'
            f'<div style="text-align:right"><b class="ed-serif-en">{_ed_esc(R.get("name",""))}</b><small>{_ed_esc(R.get("sub",""))}</small></div></div>'
            f'<div class="ed-bar"><div style="width:{lp}%;background:var(--accent2)">{f"{lp}%" if show_pct else ""}</div>'
            f'<div style="width:{rp}%;background:var(--dark)">{f"{rp}%" if show_pct else ""}</div></div></div>'
            f'<div class="ed-halves"><div><h4>{_ed_esc(b.get("left_title",""))}</h4>{tags(b.get("left_tags"), "on")}</div>'
            f'<div class="dim"><h4>{_ed_esc(b.get("right_title",""))}</h4>{tags(b.get("right_tags"), "")}</div></div>'
            + (f'<div class="ed-conclusion ed-dark"><div class="ed-in" style="max-width:760px"><p>{_ed_esc(b.get("conclusion"))}</p></div></div>' if b.get("conclusion") else "")
            + '</section>')

def ed_r_combo(b, x):
    L, R = b.get("left") or {}, b.get("right") or {}
    def box(d, res):
        lis = "".join(f"<li>{_ed_esc(t)}</li>" for t in (d.get("items") or []))
        return (f'<div class="ed-combo-c"><div class="ed-combo-box"><span class="ed-tagfill">{_ed_esc(d.get("tag",""))}</span><ul>{lis}</ul></div>'
                f'<div class="ed-arrow"></div><p class="ed-combo-res">{_ed_esc(res)}</p></div>')
    return (f'<section class="ed-sec" style="text-align:center;padding-top:80px"><div class="ed-in" style="max-width:860px">'
            f'<div class="ed-bignum">{_ed_esc(b.get("no",""))}</div><h3 class="ed-h3">{_ed_esc(b.get("title",""))}</h3>'
            f'<div class="ed-combo">{box(L, b.get("left_result",""))}<div class="ed-plus">+</div>{box(R, b.get("right_result",""))}</div>'
            '</div></section>')

def ed_r_feature_stat(b, x):
    tags = "".join(f'<span class="ed-tagline">{_ed_esc(t)}</span>' for t in (b.get("tags") or []))
    feats = "".join(f'<div class="ed-feat"><div class="ed-feat-o"></div><p>{_ed_esc(f.get("title",""))}<br><b>{_ed_esc(f.get("desc",""))}</b></p></div>'
                    for f in (b.get("features") or []))
    return (f'<section class="ed-sec" style="text-align:center;padding-top:80px"><div class="ed-in" style="max-width:860px">'
            f'<div class="ed-bignum">{_ed_esc(b.get("no",""))}</div><h3 class="ed-h3">{_ed_esc(b.get("title",""))}</h3>'
            f'<div class="ed-statbox">' + (f'<p class="ed-stat ed-serif-en">{_ed_esc(b.get("stat"))}</p>' if b.get("stat") else "")
            + f'<div>{tags}</div><p class="ed-hsub">{_ed_esc(b.get("caption",""))}</p></div>'
            + (f'<div class="ed-arrow" style="margin:0 auto"></div><p class="ed-bridge">{_ed_esc(b.get("bridge"))}</p>' if b.get("bridge") else "")
            + f'<div class="ed-feats">{feats}</div></div></section>')

def ed_r_manifesto(b, x):
    photo = x.get("photo")
    body = "".join(f"<p>{_ed_esc(t)}</p>" for t in (b.get("body") or []))
    ph = (f'<div class="ed-mani-ph" style="background:url(\'{photo}\') center top/contain no-repeat"></div>' if photo else "")
    return (f'<section class="ed-sec ed-alt" style="overflow:hidden"><div class="ed-in" style="position:relative">{ph}'
            f'<div style="max-width:{560 if photo else 820}px;position:relative;z-index:2">'
            f'<p class="ed-serif" style="color:var(--muted);font-size:20px;margin:0">{_ed_esc(b.get("kicker",""))}</p>'
            f'<h2 class="ed-h" style="margin-top:4px;font-weight:700">{_ed_esc(b.get("title",""))}</h2>'
            + (f'<div class="ed-darkbox">{_ed_esc(b.get("box"))}</div>' if b.get("box") else "")
            + f'<div class="ed-body" style="text-align:left">{body}</div>'
            + (f'<p class="ed-closing" style="text-align:left">{_ed_esc(b.get("closing"))}</p>' if b.get("closing") else "")
            + '</div></div></section>')

def ed_r_video(b, x):
    url = x.get("video", "")
    m = re.search(r"(?:youtu\.be/|v=|embed/|shorts/)([A-Za-z0-9_-]{11})", url or "")
    inner = (f'<iframe src="https://www.youtube.com/embed/{m.group(1)}" allowfullscreen style="width:100%;height:100%;border:0"></iframe>' if m else
             f'<div style="text-align:center"><p class="ed-serif-en" style="font-size:20px;margin:0">{_ed_esc(x["label"])}</p>'
             f'<p class="ed-serif-en" style="font-size:36px;margin:4px 0 20px">{_ed_esc(b.get("label") or "Orientation")}</p>'
             '<div class="ed-play"></div></div>')
    return (f'<section class="ed-sec" style="text-align:center"><div class="ed-in" style="max-width:860px">'
            + _ed_head(b.get("chapter", ""), b.get("title", ""))
            + f'<div class="ed-video">{inner}</div></div></section>')

def ed_r_lineup(b, x):
    imgs = x.get("books") or ([_ed_img(x, "key_visual")] if _ed_img(x, "key_visual") else [])
    books = b.get("books") or []
    img_html = ("".join(f'<img src="{s}" alt="">' for s in imgs[:3]) if imgs else "")
    labels = "".join(f'<div class="ed-bk"><span class="ed-tagfill">{_ed_esc(bk.get("name",""))}</span>'
                     + "".join(f"<p>{_ed_esc(t)}</p>" for t in (bk.get("items") or [])) + "</div>" for bk in books)
    struct = "".join(f'<div class="ed-struct"><span class="ed-serif-en ed-acc-l">{_ed_esc(s.get("no",""))}</span>'
                     f'<div><b class="ed-serif-en">{_ed_esc(s.get("name",""))}</b><p>{_ed_esc(s.get("desc",""))}</p></div></div>'
                     for s in (b.get("structure") or []))
    return (f'<section class="ed-sec ed-dark"><div class="ed-in" style="text-align:center;max-width:860px">'
            f'<span class="ed-pill">{_ed_esc(b.get("chapter",""))}</span>'
            f'<h2 class="ed-h ed-en" style="color:#fff;font-size:clamp(32px,4vw,50px)">{_ed_esc(b.get("title_en",""))}</h2>'
            f'<p class="ed-hsub ed-serif" style="font-size:20px">{_ed_esc(b.get("title_ko",""))}</p><div class="ed-rule"></div>'
            f'<div class="ed-lineup"><h4 class="ed-lh">교재 라인업</h4>'
            + (f'<div class="ed-bookimgs">{img_html}</div>' if img_html else "")
            + f'<div class="ed-bks" style="grid-template-columns:repeat({max(min(len(books),3),1)},1fr)">{labels}</div>'
            + (f'<h4 class="ed-lh" style="margin-top:56px">교재 구성</h4><div class="ed-structs">{struct}</div>' if struct else "")
            + '</div></div></section>')

def _ed_won(v) -> str:
    """48000 → 48,000원 (이미 쉼표·원이 있으면 그대로)"""
    t = str(v or "").strip()
    return f"{int(t):,}원" if re.fullmatch(r"\d{4,}", t) else t

def ed_r_target(b, x):
    """[v15] 수강 대상 — 이런 학생에게 (체크 카드)"""
    items = [it for it in (b.get("checks") or []) if it]
    cards = ""
    for it in items:
        t, d = (it.get("title", ""), it.get("desc", "")) if isinstance(it, dict) else (str(it), "")
        cards += (f'<div class="ed-tg-c"><div class="ed-tg-ck">✓</div><div><b>{_ed_esc(t)}</b>'
                  + (f'<span>{_ed_esc(d)}</span>' if d else "") + '</div></div>')
    return (f'<section class="ed-sec ed-alt ed-ov">{_ed_deco_motif(x, "bl", "var(--accent)", .35, 460)}<div class="ed-in">'
            + _ed_head(b.get("chapter", ""), b.get("title") or "이런 학생에게 추천합니다", b.get("sub", ""))
            + f'<div class="ed-tg">{cards}</div>'
            + (f'<p class="ed-closing" style="text-align:center">{_ed_esc(b.get("closing"))}</p>' if b.get("closing") else "")
            + '</div></section>')

def ed_r_pass_box(b, x):
    p = x.get("pass") or {}
    name = p.get("name") or "[상품명 입력]"
    inc = [t for t in (p.get("includes") or "").splitlines() if t.strip()]
    orig, price, disc = _ed_won(p.get("orig", "")), _ed_won(p.get("price", "")), str(p.get("disc", "") or "").strip()
    if re.fullmatch(r"\d+(\.\d+)?", disc):
        disc += "%"
    img = (x.get("books") or [None])[0]
    lis = "".join(f"<li>{_ed_esc(t)}</li>" for t in inc) or "<li>[구성 입력]</li>"
    return (f'<section class="ed-sec" style="text-align:center"><div class="ed-in" style="max-width:860px">'
            f'<h2 class="ed-h ed-en" style="font-size:clamp(30px,3.6vw,44px)">{_ed_esc(b.get("title") or name)}</h2><div class="ed-rule"></div>'
            f'<div class="ed-pass"><div class="ed-pass-top"><div style="text-align:left"><h4>{_ed_esc(name)}</h4><ul>{lis}</ul></div>'
            + (f'<img src="{img}" alt="" style="max-height:170px">' if img else "")
            + '</div><div class="ed-pass-bot"><div class="ed-price">'
            + (f'<span class="ed-disc">{_ed_esc(disc)}</span>' if disc else "")
            + (f'<s>{_ed_esc(orig)}</s>' if orig else "")
            + f'<b>{_ed_esc(price or "[판매가 입력]")}</b></div>'
            f'<a class="ed-buy" href="{_ehtml.escape(p.get("link") or "#")}">구매하기</a></div></div>'
            + (f'<p class="ed-hsub" style="font-size:13px">{_ed_esc(p.get("note"))}</p>' if p.get("note") else "")
            + '</div></section>')

def ed_r_benefit(b, x):
    rows = [r for r in (b.get("rows") or []) if isinstance(r, (list, tuple)) and len(r) >= 2]
    lis = "".join(f'<li><b>{_ed_esc(k)}</b> : {_ed_esc(v)}</li>' for k, v in rows)
    img = (x.get("books") or [None, None])[-1] if x.get("books") else None
    return (f'<section class="ed-sec" style="background:var(--accent2);color:#fff;--ink:#fff;--muted:rgba(255,255,255,.75)">'
            f'<div class="ed-in" style="text-align:center;max-width:820px"><p class="ed-eyebrow" style="color:#fff">BENEFIT</p>'
            f'<h2 class="ed-h" style="color:#fff">{_ed_esc(b.get("title",""))}</h2>'
            f'<div class="ed-benefit">' + (f'<img src="{img}" alt="">' if img else "") + f'<ul>{lis}</ul></div></div></section>')

def ed_r_notice(x):
    items = [t.strip(" -•") for t in (x.get("notice") or "").splitlines() if t.strip()]
    if not items:
        return ""
    return ('<section class="ed-notice"><div class="ed-in"><h4>ⓘ 유의사항</h4><ul>'
            + "".join(f"<li>{_ehtml.escape(t)}</li>" for t in items) + "</ul></div></section>")

ED_RENDERERS = {
    "target": ed_r_target,
    "hero": ed_r_hero, "prologue": ed_r_prologue, "index_tiles": ed_r_index_tiles, "course_stages": ed_r_course_stages,
    "points": ed_r_points, "statement": ed_r_statement, "quote": ed_r_quote, "three_col": ed_r_three_col, "balance": ed_r_balance, "combo": ed_r_combo,
    "feature_stat": ed_r_feature_stat, "manifesto": ed_r_manifesto, "video": ed_r_video, "lineup": ed_r_lineup,
    "pass_box": ed_r_pass_box, "benefit": ed_r_benefit,
}

def ed_css(pk: dict) -> str:
    def _mix(h, r, base="#FFFFFF"):
        return _feat_mix(h, r, base)
    return f"""
:root{{--dark:{pk['dark']};--alt:{pk['alt']};--accent:{pk['accent']};--accent2:{pk['accent2']};--accent-light:{_mix(pk['accent'],.55)};
--ink:#1E2228;--muted:#6B7280;--line:#D9DCE1;--line-strong:#B8BDC6;
--sans:'Pretendard Variable',Pretendard,-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;--ko:var(--sans);--en:{pk['en']},var(--sans);--head:{"'Noto Serif KR',serif" if pk.get('head') == 'serif' else 'var(--sans)'};--hw:{600 if pk.get('head') == 'serif' else 800};--hls:{'-.02em' if pk.get('head') == 'serif' else '-.03em'}}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}
body{{margin:0;font-family:var(--sans);color:var(--ink);background:#fff;-webkit-font-smoothing:antialiased;word-break:keep-all}}
.ed-in{{max-width:1000px;margin:0 auto;position:relative}}
.ed-sec{{padding:120px 24px;position:relative;background:#fff;color:var(--ink)}}
.ed-alt{{background:var(--alt)}}
.ed-dark{{background:var(--dark);color:#fff;--ink:#F4F5F7;--muted:rgba(255,255,255,.6);--line:rgba(255,255,255,.18);--line-strong:rgba(255,255,255,.35)}}
.ed-head{{text-align:center;margin-bottom:48px}}
.ed-pill{{display:inline-block;border:1px solid var(--line-strong);padding:5px 14px;font-family:var(--ko);font-size:12.5px;color:var(--muted);margin-bottom:6px}}
.ed-pillfill{{display:inline-block;background:var(--accent2);color:#fff;font-size:11px;letter-spacing:.12em;font-weight:700;padding:7px 18px;border-radius:99px}}
.ed-h{{font-family:var(--ko);font-weight:500;font-size:clamp(28px,3.6vw,44px);line-height:1.35;letter-spacing:-.02em;margin:14px 0 0;color:var(--ink)}}
.ed-en{{font-family:var(--en);letter-spacing:0}}
.ed-h3{{font-family:var(--ko);font-weight:500;font-size:clamp(22px,2.6vw,30px);color:var(--accent2);margin:4px 0 30px}}
.ed-hsub{{color:var(--muted);font-size:15.5px;margin:10px 0 0;line-height:1.7}}
.ed-rule{{height:1px;background:var(--line);max-width:620px;margin:26px auto 0}}
.ed-serif{{font-family:var(--ko)}}.ed-serif-en{{font-family:var(--en)}}
.ed-script{{font-family:var(--en);font-weight:600;letter-spacing:.02em}}
.ed-acc{{color:var(--accent)}}.ed-acc2{{color:var(--accent)}}.ed-acc-l{{color:var(--accent-light)}}
.ed-eyebrow{{font-family:var(--en);font-size:15px;letter-spacing:.04em;color:var(--muted);margin:0}}
.ed-body p{{font-family:var(--sans);font-weight:400;font-size:16px;line-height:1.75;color:var(--muted);margin:0 0 18px}}
.ed-closing{{font-family:var(--ko);font-weight:700;font-size:19px;color:var(--ink);margin-top:28px}}
/* hero */
.ed-hero{{position:relative;padding:100px 24px}}
.ed-wm{{font-family:var(--en);font-weight:600;line-height:.95;margin:0;letter-spacing:-.01em}}
.ed-wm-silver{{background:linear-gradient(180deg,#FFFFFF 0%,#D9DBE0 45%,#8C9099 100%);-webkit-background-clip:text;background-clip:text;color:transparent}}
.ed-wm-white{{color:#fff}}
.ed-wm-fade{{background:linear-gradient(180deg,#FFFFFF 10%,rgba(255,255,255,.55) 70%,rgba(255,255,255,.15));-webkit-background-clip:text;background-clip:text;color:transparent}}
.ed-spaced{{font-family:var(--ko);font-size:clamp(14px,1.5vw,19px);letter-spacing:.42em;color:rgba(255,255,255,.82);margin:0}}
.ed-sub-l{{font-family:var(--ko);color:rgba(255,255,255,.7);font-size:16px;margin:16px 0 0}}
.ed-note{{position:absolute;left:0;max-width:220px;text-align:left;font-family:var(--ko);font-size:13.5px;color:rgba(255,255,255,.72);z-index:2;line-height:1.6}}
.ed-note.r{{left:auto;right:0;text-align:right}}
.ed-corner{{position:absolute;font-family:var(--en);font-size:13px;letter-spacing:.08em;color:rgba(255,255,255,.65);text-transform:uppercase}}
.ed-corner.tl{{top:28px;left:40px}}.ed-corner.tr{{top:28px;right:40px}}.ed-corner.ml{{top:46%;left:40px}}.ed-corner.mr{{top:46%;right:40px}}
.ed-split{{display:grid;grid-template-columns:1fr 1.2fr;gap:40px;align-items:center}}
.ed-frame{{height:clamp(220px,32vw,330px);border-radius:14px;position:relative;overflow:hidden;filter:grayscale(.15)}}
.ed-band{{position:absolute;left:0;right:0;bottom:22%;background:color-mix(in srgb,var(--accent) 72%,transparent);color:#fff;font-family:var(--ko);font-size:clamp(16px,2vw,24px);padding:10px;letter-spacing:.3em}}
.ed-herobody p{{font-family:var(--ko);color:rgba(255,255,255,.75);font-size:15.5px;margin:6px 0}}
.ed-anchor{{display:flex;position:sticky;top:0;z-index:100;background:color-mix(in srgb,var(--accent2) 88%,transparent);-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px);overflow-x:auto;scrollbar-width:none}}.ed-anchor::-webkit-scrollbar{{display:none}}
.ed-anchor a{{flex:1 0 auto;min-width:96px;white-space:nowrap;text-align:center;color:#fff;text-decoration:none;font-family:var(--sans);font-weight:600;font-size:15px;padding:18px 14px;border-right:1px solid rgba(255,255,255,.18)}}
.ed-anchor a:last-child{{border-right:0}}.ed-anchor a:hover{{background:rgba(255,255,255,.08)}}
/* tiles & courses */
.ed-tiles{{display:grid;gap:4px;margin-top:44px}}
.ed-tile{{background:linear-gradient(180deg,#2a2d33,#16181c);border-top:2px solid var(--accent);padding:14px 10px 40px;text-align:left}}
.ed-tile span{{font-family:var(--en);font-size:13px;color:var(--muted)}}.ed-tile b{{display:block;font-family:var(--en);font-weight:500;font-size:13.5px;margin-top:8px;color:#fff}}
.ed-boxline{{border:1px solid var(--line);padding:40px 48px}}
.ed-stage{{margin-bottom:48px}}.ed-stage:last-child{{margin-bottom:0}}
.ed-stage-h{{text-align:center;font-family:var(--ko);font-size:24px;color:#fff;padding-bottom:16px;border-bottom:1px solid var(--line);margin-bottom:28px}}
.ed-stage-h span{{font-family:var(--en)}}
.ed-course{{display:grid;grid-template-columns:1fr 1.4fr;gap:28px;align-items:center;padding:16px 0}}
.ed-course-l{{text-align:center}}.ed-course-l b{{font-size:clamp(22px,2.6vw,32px);font-weight:600;color:#fff}}
.ed-course-r h4{{font-family:var(--ko);font-size:18px;margin:0 0 6px;color:#fff}}.ed-course-r p{{margin:0;color:var(--muted);font-size:14.5px;line-height:1.7}}
/* points */
.ed-diag{{background:linear-gradient(160deg,transparent 49.8%,var(--line-strong) 50%,transparent 50.2%),var(--alt)}}
.ed-points{{margin-top:60px}}
.ed-point{{display:flex;align-items:center;gap:22px;margin:0 0 56px;width:78%}}
.ed-point.r{{margin-left:auto;flex-direction:row-reverse;text-align:right}}
.ed-orb{{flex:0 0 58px;height:58px;border-radius:50%;background:radial-gradient(circle at 30% 30%,#fff,var(--accent-light) 60%,var(--accent));box-shadow:0 8px 18px rgba(0,0,0,.08)}}
.ed-plabel{{color:var(--accent);font-size:19px}}
.ed-pdesc{{margin:6px 0 4px;color:var(--muted);font-size:14.5px;line-height:1.6}}
.ed-pline{{margin:0;font-family:var(--ko);font-size:clamp(17px,1.8vw,21px);color:var(--accent2);font-weight:600}}
/* quote, cols */
.ed-quote{{position:relative;padding:10px 60px}}
.ed-quote .q{{position:absolute;top:-30px;font-family:Georgia,serif;font-size:110px;color:var(--line-strong);line-height:1}}
.ed-quote .q.l{{left:0}}.ed-quote .q.r{{right:0}}
.ed-cols{{display:grid;grid-template-columns:repeat(3,1fr);gap:28px;margin-top:56px;text-align:left}}
.ed-num{{font-family:var(--en);font-size:22px;color:var(--ink)}}
.ed-col small{{display:block;color:var(--muted);font-size:12px;margin:6px 0 2px}}
.ed-col h4{{font-family:var(--ko);font-size:22px;font-weight:500;margin:0 0 14px}}
.ed-colbar{{height:2px;background:linear-gradient(90deg,var(--accent),transparent);margin-bottom:14px}}
.ed-col p{{color:var(--muted);font-size:14px;line-height:1.7;margin:0}}
.ed-colimg{{height:110px!important;opacity:1}}
.ed-colcard{{background:#fff;border:1px solid var(--line);border-top:3px solid var(--accent);padding:30px 26px}}
.ed-bignum2{{display:block;font-family:var(--en);font-size:46px;color:var(--accent);line-height:1;margin-bottom:10px}}
.ed-hero-notes{{display:flex;justify-content:center;gap:34px;flex-wrap:wrap;margin-top:56px}}
.ed-hero-notes span{{font-family:var(--ko);font-size:14px;color:rgba(255,255,255,.7);padding-top:12px;border-top:1px solid rgba(255,255,255,.3);max-width:220px}}
.ed-prolog-img{{min-height:440px;border-radius:4px;overflow:hidden}}
.ed-pcards{{display:grid;gap:18px;margin-top:56px}}
.ed-pcard{{background:#fff;padding:34px 28px;border-bottom:3px solid var(--accent);text-align:left}}
.ed-pkw{{font-family:var(--ko);font-size:clamp(28px,3vw,38px);font-weight:600;color:var(--accent2);margin:10px 0 14px}}
.ed-ov{{overflow:hidden}}
.ed-deco{{position:absolute;z-index:0;pointer-events:none;line-height:0}}
.ed-deco-word{{position:absolute;z-index:0;pointer-events:none;font-family:var(--en);font-weight:600;font-size:clamp(110px,17vw,230px);line-height:1;
  color:transparent;-webkit-text-stroke:1px var(--line-strong);opacity:.55;letter-spacing:-.02em;white-space:nowrap}}
.ed-deco-word.on-dark{{-webkit-text-stroke:1px rgba(255,255,255,.16);opacity:1}}
.ed-sec>.ed-in,.ed-hero>.ed-in{{z-index:1}}
.ed-pkw small{{display:block;font-size:16px;font-weight:500;color:var(--ink);margin-top:6px}}
.ed-tl{{margin-top:56px;border-left:2px solid var(--accent);padding-left:0}}
.ed-tl-row{{display:grid;grid-template-columns:120px 1fr;gap:10px;padding:26px 0 26px 0;border-bottom:1px solid var(--line);text-align:left}}
.ed-tl-no{{font-family:var(--en);font-size:56px;line-height:1;color:transparent;-webkit-text-stroke:1.2px var(--accent);padding-left:28px}}
.ed-cklist{{list-style:none;margin:0;padding:0;border-top:2px solid var(--ink)}}
.ed-cklist li{{display:flex;gap:14px;align-items:flex-start;padding:20px 4px;border-bottom:1px solid var(--line);font-family:var(--ko);font-size:18px;color:var(--ink);line-height:1.55}}
.ed-ck{{flex:0 0 22px;height:22px;border-radius:50%;border:1.5px solid var(--accent);position:relative;margin-top:3px}}
.ed-ck:after{{content:'';position:absolute;left:6px;top:3px;width:6px;height:10px;border:solid var(--accent);border-width:0 2px 2px 0;transform:rotate(45deg)}}
.ed-zzs{{margin-top:56px;display:grid;gap:28px}}
.ed-zz{{display:grid;grid-template-columns:1.1fr 1fr;gap:40px;align-items:center;text-align:left}}
.ed-zz.rev .ed-zz-img{{order:2}}
.ed-zz-img{{height:260px;border-radius:4px;overflow:hidden}}
.ed-zz-t small{{display:block;color:var(--muted);font-size:13px;margin-bottom:4px}}
.ed-zz-t h4{{font-family:var(--ko);font-size:26px;font-weight:600;margin:0 0 12px;color:var(--ink)}}
.ed-zz-t p{{color:var(--muted);font-size:15.5px;line-height:1.8;margin:0}}
.ed-stline{{width:1px;height:70px;background:var(--accent);margin:0 auto 34px}}
/* balance */
.ed-barlabels{{display:flex;justify-content:space-between;margin:44px 0 10px;text-align:left}}
.ed-barlabels b{{display:block;font-size:17px}}.ed-barlabels small{{color:var(--muted);font-size:12px}}
.ed-bar{{display:flex;height:56px;border-radius:99px;overflow:hidden;color:#fff;font-family:var(--en);font-size:22px}}
.ed-bar div{{display:flex;align-items:center;justify-content:center}}
.ed-halves{{display:grid;grid-template-columns:1fr 1fr;margin:70px -24px 0}}
.ed-halves>div{{padding:56px 30px;text-align:center;background:rgba(0,0,0,.03)}}
.ed-halves>div.dim{{background:rgba(0,0,0,.06);opacity:.7}}
.ed-halves h4{{font-family:var(--ko);font-weight:500;font-size:22px;color:var(--ink);margin:0 0 26px}}
.ed-bubble{{display:inline-flex;align-items:center;justify-content:center;width:96px;height:96px;border-radius:50%;margin:5px;font-size:13px;
  background:#C9CED6;color:#fff}}.ed-bubble.on{{background:var(--accent2)}}
.ed-conclusion{{padding:64px 24px;text-align:center;margin:0 -24px}}.ed-conclusion p{{font-family:var(--ko);font-size:clamp(18px,2vw,24px);line-height:1.7;margin:0}}
/* combo, stat */
.ed-bignum{{font-family:var(--en);font-size:44px;color:var(--line-strong);line-height:1;border-bottom:1px solid var(--line);padding-bottom:6px}}
.ed-combo{{display:flex;align-items:flex-start;justify-content:center;gap:24px}}
.ed-combo-c{{flex:0 1 300px}}
.ed-combo-box{{background:#fff;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.06);padding:26px 30px;min-height:220px}}
.ed-combo-box ul{{list-style:none;padding:0;margin:18px auto 0;text-align:left;display:table}}
.ed-combo-box .ed-tagfill{{display:table;margin:0 auto}}
.ed-combo-box li{{font-size:14.5px;color:var(--muted);margin:5px 0}}.ed-combo-box li:before{{content:'· '}}
.ed-tagfill{{display:inline-block;background:var(--accent);color:#fff;padding:7px 22px;border-radius:6px;font-weight:700;font-size:14px}}
.ed-plus{{font-size:40px;color:var(--muted);margin-top:90px;font-weight:200}}
.ed-arrow{{width:0;height:0;border-left:26px solid transparent;border-right:26px solid transparent;border-top:22px solid var(--line);margin:0 auto 12px}}
.ed-combo-res{{font-family:var(--ko);color:var(--accent2);font-size:16px;line-height:1.6}}
.ed-statbox{{background:#fff;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.06);padding:30px;max-width:620px;margin:0 auto 18px}}
.ed-stat{{font-size:30px;color:var(--accent);margin:0 0 14px}}
.ed-tagline{{display:inline-block;border:1px solid var(--accent-light);color:var(--accent);padding:5px 16px;margin:3px;font-size:13.5px}}
.ed-bridge{{font-family:var(--ko);font-size:18px;color:var(--ink);font-weight:600}}
.ed-feats{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-top:30px}}
.ed-feat-o{{width:120px;height:120px;border-radius:50%;margin:0 auto 14px;background:radial-gradient(circle at 35% 35%,#fff,var(--accent-light) 70%)}}
.ed-feat p{{font-size:14px;color:var(--muted);line-height:1.6}}.ed-feat b{{color:var(--ink)}}
/* manifesto, video, lineup, pass */
.ed-mani-ph{{position:absolute;right:-40px;top:-60px;bottom:-120px;width:46%}}
.ed-darkbox{{display:inline-block;background:var(--dark);color:#fff;font-family:var(--ko);font-size:clamp(17px,1.8vw,22px);padding:8px 16px;margin:22px 0 10px}}
.ed-video{{aspect-ratio:16/9;background:#222;display:flex;align-items:center;justify-content:center;color:#fff}}
.ed-play{{width:0;height:0;margin:0 auto;border-top:26px solid transparent;border-bottom:26px solid transparent;border-left:44px solid rgba(255,255,255,.75)}}
.ed-lineup{{text-align:left;margin-top:56px}}
.ed-lh{{font-family:var(--ko);font-weight:500;font-size:22px;color:#fff;border-bottom:1px solid var(--line);padding-bottom:12px;margin:0 0 26px}}
.ed-bookimgs{{text-align:center;margin-bottom:20px}}.ed-bookimgs img{{height:230px;margin:0 6px;filter:drop-shadow(0 18px 24px rgba(0,0,0,.4))}}
.ed-bks{{display:grid;gap:14px}}.ed-bk{{text-align:center}}.ed-bk p{{color:var(--muted);font-size:13.5px;margin:6px 0}}
.ed-structs{{padding-left:30%}}.ed-struct{{display:flex;gap:12px;margin-bottom:22px}}
.ed-struct span{{font-size:30px;line-height:1}}.ed-struct b{{font-size:22px;color:#fff;font-weight:500}}.ed-struct p{{color:var(--muted);font-size:13.5px;margin:6px 0 0}}
.ed-pass{{border:1px solid var(--line-strong);border-radius:10px;overflow:hidden;margin:40px auto 14px;text-align:left}}
.ed-pass-top{{display:flex;justify-content:space-between;align-items:center;gap:20px;padding:28px 34px}}
.ed-pass-top h4{{font-family:var(--ko);font-size:20px;margin:0 0 10px;color:var(--accent2)}}
.ed-pass-top ul{{margin:0;padding-left:18px;color:var(--muted);font-size:13.5px;line-height:1.8}}
.ed-pass-bot{{display:flex;align-items:stretch}}
.ed-price{{flex:1;display:flex;align-items:center;gap:14px;padding:18px 34px;background:var(--alt)}}
.ed-price s{{color:var(--muted);font-size:18px}}.ed-price b{{font-size:28px;color:var(--accent2)}}
.ed-disc{{background:var(--accent2);color:#fff;font-weight:800;font-size:14px;padding:8px 12px;clip-path:polygon(0 0,100% 0,85% 100%,0 100%);padding-right:22px}}
.ed-buy{{flex:0 0 38%;display:flex;align-items:center;justify-content:center;background:var(--dark);color:#fff;text-decoration:none;font-weight:800;font-size:20px;clip-path:polygon(8% 0,100% 0,100% 100%,0 100%)}}
.ed-benefit{{display:flex;gap:40px;align-items:center;justify-content:center;margin-top:40px;text-align:left}}
.ed-benefit img{{width:200px;box-shadow:0 18px 30px rgba(0,0,0,.35)}}.ed-benefit ul{{list-style:none;padding:0;margin:0}}
.ed-benefit li{{font-size:15px;line-height:1.7;margin:6px 0;color:rgba(255,255,255,.9)}}.ed-benefit li:before{{content:'· '}}
.ed-notice{{background:#0F0F10;color:rgba(255,255,255,.6);padding:50px 24px}}
.ed-notice h4{{color:#fff;margin:0 0 14px;font-size:15px}}.ed-notice ul{{margin:0;padding-left:18px}}.ed-notice li{{font-size:13px;line-height:1.9}}
.ed-side{{position:fixed;right:0;top:40%;z-index:50;opacity:0;pointer-events:none;transition:opacity .3s;background:rgba(20,22,26,.92);padding:10px 0;border-radius:8px 0 0 8px}}
.ed-side.on{{opacity:1;pointer-events:auto}}
.ed-side a{{display:block;color:rgba(255,255,255,.75);text-decoration:none;font-size:12px;padding:7px 16px;font-family:var(--ko)}}.ed-side a:hover{{color:#fff}}
@media(max-width:860px){{
 .ed-sec{{padding:80px 20px}}.ed-split,.ed-course,.ed-halves,.ed-cols,.ed-feats{{grid-template-columns:1fr!important}}
 .ed-split div{{text-align:center!important}}.ed-point{{width:100%}}.ed-tiles{{grid-template-columns:repeat(2,1fr)!important}}
 .ed-split img{{max-height:260px!important}}
 .ed-pcards{{grid-template-columns:1fr!important}}.ed-zz{{grid-template-columns:1fr!important}}.ed-zz.rev .ed-zz-img{{order:0}}
 .ed-tl-row{{grid-template-columns:70px 1fr}}.ed-tl-no{{font-size:38px;padding-left:14px}}.ed-deco-word{{font-size:90px}}.ed-prolog-img{{min-height:260px}}
 .ed-note,.ed-corner.ml,.ed-corner.mr,.ed-side,.ed-mani-ph{{display:none}}.ed-boxline{{padding:28px 20px}}
 .ed-combo{{flex-direction:column;align-items:center}}.ed-plus{{margin:0}}.ed-structs{{padding-left:0}}
 .ed-pass-top,.ed-pass-bot,.ed-benefit{{flex-direction:column}}.ed-buy{{padding:18px;clip-path:none}}.ed-anchor a{{font-size:13.5px;padding:15px 12px;min-width:auto}}
}}
/* [v15] 한글 제목 서체 · 굵기 */
.ed-h,.ed-h3,.ed-pkw,.ed-zz-t h4,.ed-col h4,.ed-halves h4,.ed-lh,.ed-stage-h,.ed-conclusion p,.ed-pline{{font-family:var(--head);font-weight:var(--hw);letter-spacing:var(--hls)}}
.ed-h{{line-height:1.3}}
/* [v15] 수강 대상 */
.ed-tg{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;max-width:880px;margin:0 auto}}
.ed-tg-c{{display:flex;gap:16px;align-items:flex-start;background:#fff;border:1px solid var(--line);padding:24px 24px;text-align:left}}
.ed-dark .ed-tg-c,.ed-alt .ed-tg-c{{background:transparent}}
.ed-tg-ck{{flex:0 0 30px;height:30px;border-radius:50%;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:15px}}
.ed-tg-c b{{display:block;font-size:17px;font-weight:700;color:var(--ink);line-height:1.5}}.ed-tg-c span{{display:block;font-size:14.5px;color:var(--muted);line-height:1.7;margin-top:4px}}
@media(max-width:720px){{.ed-tg{{grid-template-columns:1fr}}}}
"""

ED_WRAP_ID = "dm-promo-wrap"

def _ed_scope_css(css: str, scope: str = "#" + ED_WRAP_ID) -> str:
    """[v15] 모든 선택자 앞에 #dm-promo-wrap — 사이트 GNB·푸터에 영향 없게.
    :root/html/body → 래퍼 자신, * → 래퍼 안쪽 전체. @media 안쪽도 처리, @keyframes는 그대로."""
    out, i, n = [], 0, len(css)
    def _pref(sel):
        parts = []
        for one in sel.split(","):
            t = one.strip()
            if not t:
                continue
            if t in (":root", "html", "body"):
                parts.append(scope)
            elif t == "*":
                parts += [scope, f"{scope} *"]
            elif t.startswith(scope):
                parts.append(t)
            else:
                parts.append(f"{scope} {t}")
        return ",".join(parts)
    def _block(txt):
        res, k = [], 0
        while k < len(txt):
            ob = txt.find("{", k)
            if ob == -1:
                res.append(txt[k:]); break
            head = txt[k:ob].strip()
            depth, m = 1, ob + 1
            while m < len(txt) and depth:
                depth += {"{": 1, "}": -1}.get(txt[m], 0); m += 1
            body = txt[ob + 1:m - 1]
            if head.startswith("@media") or head.startswith("@supports"):
                res.append(f"{head}{{{_block(body)}}}")
            elif head.startswith("@"):
                res.append(f"{head}{{{body}}}")
            else:
                res.append(f"{_pref(head)}{{{body}}}")
            k = m
        return "".join(res)
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = css.replace("html{scroll-behavior:smooth}", "")
    return _block(css)

def _ed_img_dims(uri: str):
    try:
        from PIL import Image
        import io
        m = re.match(r"data:image/\w+;base64,(.+)", uri, re.S)
        im = Image.open(io.BytesIO(base64.b64decode(m.group(1))))
        return im.width, im.height
    except Exception:
        return 1000, 560

ED_IMG_NAMES = {"hero_bg": "히어로 배경", "key_visual": "키 비주얼", "texture": "섹션 텍스처"}

def _ed_img_registry(x: dict) -> list:
    """(data URI, 파일명, 설명) 목록"""
    reg = []
    if x.get("photo"):
        reg.append((x["photo"], "instructor", "강사 사진(누끼)"))
    for k, u in enumerate(x.get("books") or []):
        reg.append((u, f"book_{k + 1}", f"교재·키비주얼 {k + 1}"))
    for slot, u in (x.get("imgs") or {}).items():
        if u:
            reg.append((u, slot, ED_IMG_NAMES.get(slot, slot)))
    return reg

def _ed_swap_images(html: str, x: dict, mode: str) -> str:
    """mode: embed(그대로) / path(images/파일) / placeholder(placehold.co + 주석)"""
    if mode == "embed":
        return html
    notes = []
    for uri, name, desc in _ed_img_registry(x):
        if not uri or uri not in html:
            continue
        w, h = _ed_img_dims(uri)
        ext = "png" if uri.startswith("data:image/png") else "jpg"
        if mode == "path":
            url = f"images/{name}.{ext}"
        else:
            url = f"https://placehold.co/{w}x{h}/16181c/FFFFFF?text={desc.replace(' ', '+')}+({w}x{h})"
        # <img> 바로 앞에 교체 안내 주석
        html = re.sub(r'(<img\b[^>]*?src=")' + re.escape(uri) + '"',
                      lambda m: f'<!-- [이미지 교체 영역] {desc} · 권장 사이즈: {w}x{h}px · {name}.{ext} -->' + m.group(1) + url + '"', html)
        html = html.replace(uri, url)      # CSS 배경(url(...)) 등 나머지
        notes.append(f"  - {name}.{ext} : {desc} · 권장 {w}x{h}px")
    if notes:
        head = "<!-- [이미지 교체 목록]\n" + "\n".join(notes) + "\n  ※ 실제 이미지 경로(CDN 주소)로 바꿔 넣으세요. 강사 사진은 실제 촬영본만 사용 -->\n"
        html = html.replace(f'<div id="{ED_WRAP_ID}">', head + f'<div id="{ED_WRAP_ID}">', 1)
    return html

def _ed_font_links(pk: dict) -> str:
    fam = ED_EN_FONTS.get(pk.get("en"), "Playfair+Display:wght@500;600;700")
    serif = "&family=Noto+Serif+KR:wght@500;600;700" if pk.get("head") == "serif" else ""
    return ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            f'<link href="https://fonts.googleapis.com/css2?family={fam}{serif}&display=swap" rel="stylesheet">'
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">')

def ed_build_html(plan: dict, x: dict, export: bool = False, img_mode: str = "embed", fragment: bool = False) -> str:
    """미리보기·내보내기 공통.
    img_mode: embed(이미지 내장) / path(images/ 경로, 전달 패키지용) / placeholder(자리표시 + 교체 주석)
    fragment: True면 <html>·<head>·<body> 없이 CMS 본문에 붙여넣는 코드만"""
    pk = dict(ED_PACKS.get(plan.get("pack"), ED_PACKS["noir_navy"]))
    if plan.get("head") in ("sans", "serif"):
        pk["head"] = plan["head"]
    blocks = plan.get("blocks") or []
    x = dict(x); x["motif"] = " ".join(str((plan.get("kit") or {}).get(k, "")) for k in ("motif", "concept_en"))
    x["concept_en"] = str((plan.get("kit") or {}).get("concept_en", "")); x["deco"] = plan.get("deco", True)
    _show = lambda b: not b.get("hidden") and (b.get("type") in ("hero", "pass_box", "video") or not _ed_is_empty(b))
    navs, seen = [], set()
    for i, b in enumerate(blocks):
        lab = str(b.get("nav") or "").strip()
        if lab and b.get("type") != "hero" and _show(b) and lab not in seen:
            seen.add(lab); navs.append((f"ed-b{i}", lab))
    secs = []
    for i, b in enumerate(blocks):
        if not _show(b):
            continue
        fn = ED_RENDERERS.get(b.get("type"))
        if not fn:
            continue
        try:
            h = fn(b, x)
        except Exception as e:
            h = "" if export else f'<div style="padding:12px;color:#c00;font-size:12px">[{b.get("type")}] 렌더 오류: {_ehtml.escape(str(e))}</div>'
        if h:
            secs.append(f'<div id="ed-b{i}">{h}</div>')
            if b.get("type") == "hero":
                secs.append(ed_r_anchor_bar(navs))
    css = _ed_scope_css(ed_css(pk)) + f"#{ED_WRAP_ID}{{overflow-x:clip;scroll-behavior:smooth}}"
    inner = f'<div id="{ED_WRAP_ID}">{"".join(secs)}{ed_r_notice(x)}</div>'
    if fragment:
        out = ("<!-- ▼ 대성마이맥 PR 페이지 본문 시작 — 이 블록 전체를 에디터의 HTML(소스) 모드에 붙여넣으세요 -->\n"
               + _ed_font_links(pk) + f"\n<style>{css}</style>\n" + inner + "\n<!-- ▲ PR 페이지 본문 끝 -->")
    else:
        title = strip_hanja(str(x.get("label", "")))
        out = ('<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
               f'<title>{_ehtml.escape(title)}</title>{_ed_font_links(pk)}<style>{css}</style>'
               '<style>body{margin:0}</style></head><body>' + inner + '</body></html>')
    return _ed_swap_images(out, x, img_mode)


# ── AI: 컨셉 키트 + 구성 ──────────────────────────────────
def _ed_inputs_text() -> str:
    g = st.session_state.get
    rows = [
        f"- 강사: {g('ed_inst') or '(미입력)'} / 과목: {g('ed_subject')} / 대상: {g('ed_target')}",
        f"- 강좌명(워드마크): {g('ed_label') or '(미입력)'}",
        f"- 기획 메모·원고: {g('ed_memo') or '(없음)'}",
        f"- 강좌 라인업(강좌명 목록): {g('ed_courses') or '(없음)'}",
        f"- 교재 정보: {g('ed_books') or '(없음)'}",
        f"- 구매 상품: {g('ed_pass_name') or '(없음)'} / 구성: {(g('ed_pass_inc') or '').replace(chr(10), ', ') or '(없음)'}",
        f"- 혜택·이벤트: {g('ed_benefit') or '(없음)'}",
    ]
    return "\n".join(rows)

ED_EXAMPLE = json.dumps({'kit': {'concept_en': 'STEP', 'verb': '오르다', 'motif': '계단·디딤돌', 'keywords': ['어휘', '구문', '완독'], 'antithesis': '어려운 건 덜고, 쉬운 것부터 쌓고'}, 'blocks': [{'type': 'hero', 'variant': 'split_motif', 'kicker': '영어가 가장 막막한 과목이라면', 'sub': '수능 영어, 첫 계단부터 다시', 'wordmark': 'KEY STEP'}, {'type': 'prologue', 'nav': '프롤로그', 'script': 'Prologue', 'title': '첫 계단의 영어', 'sub': '6~8등급에게 필요한 건 더 높은 계단이 아닙니다', 'body': ['단어가 낯설고 문장이 끊겨 보이면, 수능 지문은 펼치는 순간부터 벽이 됩니다.', 'KEY STEP은 중학 영어 수준에서 출발해 어휘, 구문, 독해를 한 칸씩 쌓아 올리는 입문 강좌입니다.'], 'closing': '높이보다 순서. 한 계단씩 오릅니다.'}, {'type': 'points', 'nav': '기획 의도', 'title_en': 'KEY STEP', 'title_ko': '기획 의도', 'points': [{'label': 'Step Point 01', 'desc': '수능에 반복해서 나오는 기초 어휘부터 정리합니다.', 'line': '낯선 단어부터 줄여 가는', 'keyword': '어휘'}, {'label': 'Step Point 02', 'desc': '주어와 동사를 찾아 문장의 뼈대를 세웁니다.', 'line': '문장의 뼈대를 세우는', 'keyword': '구문'}, {'label': 'Step Point 03', 'desc': '짧은 지문부터 끝까지 읽어 내는 경험을 쌓습니다.', 'line': '지문을 끝까지 읽어 내는', 'keyword': '완독'}]}]}, ensure_ascii=False)

def ed_brief() -> str:
    concept = st.session_state.get("ed_concept", "").strip()
    return "\n".join([
        "당신은 대성마이맥 컨텐츠기획실의 시니어 카피라이터 겸 PR 페이지 기획자입니다.",
        ED_STYLE_GUIDE, ED_CRAFT_GUIDE, season_prompt_block(),
        "[강좌 정보 — 여기에 없는 사실·숫자·가격·기간은 쓰지 않는다]", _ed_inputs_text(),
        (f"[컨셉 지정] {concept} — 이 단어/이미지로 컨셉 키트를 만든다." if concept else ""),
        "[모범 예시 — 6~8등급 입문 강좌 'KEY STEP'의 앞부분. 컨셉 동사·「키워드」가 이어지는 방식과 말맛만 참고하고, 문장은 재사용하지 말 것]",
        ED_EXAMPLE,
    ])

def _ed_block_catalog() -> str:
    return "\n".join(f"- {k}: {v[0]}\n  {v[1]}" for k, v in ED_BLOCK_SPECS.items())

def ed_generate_plan(avoid: str = "") -> dict:
    packs = ", ".join(f"{k}({v['name']})" for k, v in ED_PACKS.items())
    prompt = (
        f"{ed_brief()}\n\n[블록 라이브러리]\n{_ed_block_catalog()}\n\n"
        "[구성 규칙]\n"
        "1. 첫 블록은 hero. 이후 6~9개 블록을 이 강좌의 정보량과 컨셉에 맞게 골라 순서를 정한다.\n"
        "2. 정보가 없는 블록(lineup, balance, feature_stat, benefit, index_tiles 등)은 쓰지 않는다.\n"
        "3. 구매 상품 정보가 있으면 pass_box를, 혜택 정보가 있으면 benefit을 뒤쪽에 둔다.\n"
        "4. 같은 type은 한 번만(combo·feature_stat만 예외). layout은 a/b/c를 섞어 밝은 섹션과 어두운 섹션이 번갈아 나오게. statement는 섹션 사이 전환용으로 1번.\n"
        "4-1. 순서: hero → prologue → (points/quote/statement/three_col 등 강좌 설명) → video → lineup → pass_box → benefit. 구매 박스는 맨 뒤.\n"
        "5. 모든 섹션 제목은 컨셉 키트의 동사·키워드로 이어지게 쓴다.\n"
        f"6. pack은 다음 중 컨셉에 어울리는 하나: {packs}\n"
        + (f"7. 이전 구성과 다르게: {avoid}\n" if avoid else "")
        + '\nJSON 하나만 반환:\n{"kit":{"concept_en":"컨셉 영단어","verb":"컨셉 동사 (예: 설계하다)","motif":"시각 모티프",'
        '"keywords":["「키워드」1","2","3"],"antithesis":"대구 한 줄"},"pack":"팩 키","blocks":[ {블록}, ... ]}'
    )
    st.session_state["_last_ctx"] = _ed_inputs_text()   # 품질 검사에서 '입력된 숫자'로 인정
    plan = safe_json(call_ai(prompt, max_tokens=7000, temperature=0.85))
    plan = ed_polish(plan)
    plan = ed_copy_workshop(plan)
    plan["blocks"] = proofread_copy(plan["blocks"], st.session_state.get("ed_label", ""))
    return plan


# ── [v14] 모든 섹션을 먼저 펼쳐 놓기 ─────────────────────────
def ed_block_needs() -> dict:
    """블록 type → 부족한 입력 정보 이름 ('' 이면 바로 작성 가능). 정보 없이 쓰면 내용을 지어내게 되는 블록만."""
    g = st.session_state.get
    memo = str(g("ed_memo") or "")
    courses = [t for t in str(g("ed_courses") or "").splitlines() if t.strip()]
    has_books = bool(str(g("ed_books") or "").strip() or g("ed_books_img"))
    return {
        "index_tiles": "" if len(courses) >= 3 else "강좌 라인업 3개 이상",
        "course_stages": "" if courses else "강좌 라인업",
        "balance": "" if re.search(r"\d+\s*%", memo) else "기획 메모에 비율(%)",
        "feature_stat": "" if re.search(r"\d+\s*(강|회|문항|문제|주|권|세트|Sessions?|Questions?)", memo, re.I) else "기획 메모에 회차·문항 수",
        "video": "" if g("ed_video") else "OT 영상 링크",
        "lineup": "" if has_books else "교재 정보",
        "pass_box": "" if g("ed_pass_name") else "구매 상품명",
        "benefit": "" if g("ed_benefit") else "혜택·이벤트",
    }

def _ed_is_empty(b: dict) -> bool:
    return not any(v not in ("", [], {}, None) for k, v in b.items()
                   if k not in ("type", "layout", "variant", "nav", "hidden") and not str(k).startswith("_"))

def _ed_auto_layouts(blocks: list) -> list:
    """레이아웃이 비었으면 a/b/c를 돌려가며 — 밝은/어두운 섹션이 번갈아 나오게"""
    seq = ["b", "a", "c", "a", "b", "c"]
    j = 0
    for b in blocks:
        if b.get("type") in ED_LAYOUT_BLOCKS:
            n = len(ED_LAYOUT_BLOCKS[b["type"]].split(" / "))
            if b.get("layout") not in ("a", "b", "c")[:n]:
                b["layout"] = seq[j % len(seq)] if seq[j % len(seq)] in ("a", "b", "c")[:n] else "a"
            j += 1
    return blocks

def ed_generate_full(avoid: str = "") -> dict:
    """[v14] 블록 라이브러리의 모든 섹션을 한 번에 작성 → MD가 순서·표시를 직접 고른다.
    정보가 없는 섹션은 내용을 지어내지 않고 '숨김 + 필요한 정보' 상태로 자리만 만들어 둔다."""
    needs = ed_block_needs()
    ai_types = [t for t in ED_FULL_ORDER if t != "hero" and not needs.get(t)]
    n1 = 5 if _groq_free() else 7          # 무료 요금제는 한 번에 쓸 양을 줄여 여러 번 나눠 씀
    g1, rest = ai_types[:n1], ai_types[n1:]
    chunks = [rest[k:k + n1] for k in range(0, len(rest), n1)]
    packs = ", ".join(f"{k}({v['name']})" for k, v in ED_PACKS.items())
    cat = lambda ts: "\n".join(f"- {t}: {ED_BLOCK_SPECS[t][0]}\n  {ED_BLOCK_SPECS[t][1]}" for t in ["hero"] + ts if t in ED_BLOCK_SPECS)
    rules = ("[작성 규칙]\n"
             "- 각 섹션은 페이지에서 서로 다른 역할을 한다. 같은 문장·같은 표현을 다른 섹션에서 반복하지 않는다.\n"
             "- prologue는 '왜 이 강좌인가', points/quote는 '어떻게 가르치는가', three_col은 '무엇이 다른가', manifesto는 '강사의 목소리'.\n"
             "- 모든 섹션 제목은 컨셉 키트의 동사·키워드로 이어지게, 설명은 평이하게.\n"
             "- MD가 이 중 일부만 골라 쓰므로, 어느 섹션을 빼도 페이지가 어색하지 않게 각 섹션을 독립적으로 쓴다.\n")
    st.session_state["_last_ctx"] = _ed_inputs_text()
    p1 = (f"{ed_brief()}\n\n[작성할 블록 — 아래 type을 이 순서대로 하나씩, 빠짐없이]\n{cat(g1)}\n\n{rules}"
          f"- pack은 다음 중 컨셉에 어울리는 하나: {packs}\n" + (f"- 이전 결과와 다른 컨셉으로: {avoid}\n" if avoid else "")
          + '\nJSON 하나만 반환:\n{"kit":{"concept_en":"컨셉 영단어","verb":"컨셉 동사","motif":"시각 모티프",'
          '"keywords":["「키워드」1","2","3"],"antithesis":"대구 한 줄"},"pack":"팩 키","blocks":[hero, ' + ", ".join(g1) + ']}')
    plan = safe_json(call_ai(p1, max_tokens=7000, temperature=0.85))
    blocks = [b for b in (plan.get("blocks") or []) if isinstance(b, dict)]
    for g2 in chunks:
        done = [{k: b.get(k) for k in ("type", "title", "title_ko", "kicker", "line", "closing") if b.get(k)} for b in blocks]
        p2 = (f"{ed_brief()}\n\n[이 페이지의 컨셉 키트]\n{json.dumps(plan.get('kit', {}), ensure_ascii=False)}\n"
              f"[이미 쓴 섹션 — 이 표현들과 겹치지 않게]\n{json.dumps(done, ensure_ascii=False)}\n\n"
              f"[작성할 블록 — 아래 type을 이 순서대로 하나씩, 빠짐없이]\n{cat(g2)}\n\n{rules}"
              '\nJSON 하나만 반환:\n{"blocks":[' + ", ".join(g2) + ']}')
        try:
            more = safe_json(call_ai(p2, max_tokens=6000, temperature=0.85))
            blocks += [b for b in (more.get("blocks") or []) if isinstance(b, dict)]
        except Exception:
            pass
    by_type = {}
    for b in blocks:
        by_type.setdefault(b.get("type"), b)
    final = []
    for t in ED_FULL_ORDER:
        if t in by_type:
            b = by_type[t]
        elif needs.get(t):
            b = {"type": t, "hidden": True, "_needs": needs[t]}
        else:
            b = {"type": t, "hidden": True, "_needs": "다시 쓰기"}   # AI가 빠뜨린 블록 — 자리만
        final.append(b)
    plan["blocks"] = _ed_auto_layouts(final)
    plan["full"] = True
    plan = ed_polish(plan)
    plan = ed_copy_workshop(plan)
    plan["blocks"] = proofread_copy(plan["blocks"], st.session_state.get("ed_label", ""))
    return plan


# ── [v14] 카피 워크숍: 핵심 문구마다 후보 3개 → 디렉터가 하나 고르기 ───────────
def _ed_cand_ok(t: str, orig: str) -> bool:
    if not isinstance(t, str) or not t.strip():
        return False
    season, facts = get_season(), _user_facts()
    if any(not _allowed_hit(m.group(0), season, facts) for m in list(_DDAY_ANY_RE.finditer(t)) + list(_FAKE_NUM_RE.finditer(t))):
        return False
    if any(w in t for w in CLICHE_WORDS) or any(ph in t for ph in ED_COPIED_PHRASES):
        return False
    return len(t) <= max(44, int(len(orig or "") * 1.8))

def ed_copy_workshop(plan: dict, only_idx=None) -> dict:
    """히어로·제목·선언 같은 핵심 문구마다 서로 다른 각도의 후보 3개를 쓰고,
    크리에이티브 디렉터 기준으로 하나를 고른다. 나머지 후보는 블록 편집에서 바꿔 끼울 수 있게 보관."""
    if not st.session_state.get("api_key"):
        return plan
    blocks = plan.get("blocks") or []
    fields, flat = [], {}
    for i, b in enumerate(blocks):
        if only_idx is not None and i != only_idx:
            continue
        if b.get("hidden") and only_idx is None:
            continue
        for k, role in ED_KEY_FIELDS.get(b.get("type"), {}).items():
            v = b.get(k)
            if isinstance(v, str) and v.strip():
                fid = f"f{len(fields)}"
                fields.append((i, k))
                ctx_txt = " / ".join(str(vv) for kk, vv in b.items()
                                     if isinstance(vv, str) and kk not in ("type", "layout", "variant", "nav", k) and vv.strip())[:160]
                flat[fid] = {"섹션": ED_BLOCK_SPECS.get(b.get("type"), ("",))[0].split(" (")[0], "역할": role,
                             "현재": v, "같은 섹션의 다른 문구": ctx_txt}
    if not fields:
        return plan
    kit = plan.get("kit") or {}
    others = [b.get(k) for b in blocks for k in ED_KEY_FIELDS.get(b.get("type"), {}) if isinstance(b.get(k), str)] if only_idx is not None else []
    prompt = (
        f"{ed_brief()}\n\n[이 페이지의 컨셉 키트]\n{json.dumps(kit, ensure_ascii=False)}\n"
        + (f"[페이지의 다른 핵심 문구 — 겹치지 않게]\n{json.dumps(others, ensure_ascii=False)}\n" if others else "")
        + "\n당신은 이 페이지의 크리에이티브 디렉터입니다. 아래 핵심 문구마다 두 단계로 작업하세요.\n"
        "1) 서로 다른 각도의 후보 3개를 새로 씁니다.\n"
        "   A안: 이 강좌를 들을 학생의 실제 고민·속마음에서 출발\n"
        "   B안: 강좌가 실제로 하는 일을 구체적이고 정확하게\n"
        f"   C안: 컨셉어({kit.get('concept_en', '')}·{kit.get('verb', '')})를 한 번만, 절제해서\n"
        "2) '현재' 문구까지 4개 중 가장 좋은 것을 고릅니다. 기준 —\n"
        "   ① 읽자마자 뜻이 통하는가 ② 구체적인가 ③ 다른 강좌에 붙이면 어색한가(이 강좌에만 맞는 말인가)\n"
        "   ④ 과장·상투어·억지 비유가 없는가 ⑤ 소리 내 읽었을 때 리듬이 좋은가\n"
        "- 길이는 현재 문구와 비슷하게(±40%). 숫자·사실은 강좌 정보에 있는 것만. 「 」·[[ ]] 표시는 써도 된다.\n"
        "- 문구끼리도 비교해, 같은 어미·같은 문장 구조가 페이지에서 반복되지 않게 고른다.\n"
        "- 후보는 그 칸의 '섹션'과 '역할'에만 맞게 쓴다. 히어로 첫 줄과 메시지 섹션 윗줄처럼 칸이 다르면 후보도 완전히 달라야 하며, "
        "한 칸의 후보를 다른 칸에 다시 쓰지 않는다. '같은 섹션의 다른 문구'와 자연스럽게 이어져야 한다.\n\n"
        f"{json.dumps(flat, ensure_ascii=False)}\n\n"
        'JSON만 반환: {"f0":{"cands":["A안","B안","C안"],"pick":0,"why":"고른 이유 한 줄"}, ...}  (pick: 0=현재 유지, 1~3=후보 번호)'
    )
    try:
        res = safe_json(call_ai(prompt, max_tokens=5000, temperature=0.8))
    except Exception:
        return plan
    used = set()                       # 다른 칸에 이미 나온 후보는 빼기 (칸마다 다른 후보만 남게)
    for b in blocks:
        for kk, vv in b.items():
            if isinstance(vv, str) and kk in ED_KEY_FIELDS.get(b.get("type"), {}):
                used.add(re.sub(r"\s", "", vv))
    for n, (i, k) in enumerate(fields):
        r = res.get(f"f{n}")
        if not isinstance(r, dict):
            continue
        orig = blocks[i][k]
        cands = [strip_hanja(str(c)).strip() for c in (r.get("cands") or [])][:3]
        ok = []
        for c in cands:
            sig = re.sub(r"\s", "", c)
            if _ed_cand_ok(c, orig) and c != orig and sig not in used:
                ok.append(c); used.add(sig)
        try:
            pick = int(r.get("pick", 0))
        except Exception:
            pick = 0
        chosen = cands[pick - 1] if 1 <= pick <= len(cands) and cands[pick - 1] in ok else orig
        opts = []
        for c in [chosen, orig] + ok:
            if c and c not in opts:
                opts.append(c)
        blocks[i][k] = chosen
        if len(opts) > 1:
            blocks[i].setdefault("_alts", {})[k] = {"opts": opts, "why": str(r.get("why", ""))[:80]}
    plan["blocks"] = blocks
    return plan

def ed_polish(plan: dict) -> dict:
    blocks = plan.get("blocks") or []
    wrapped = {f"b{i}": b for i, b in enumerate(blocks)}
    wrapped = polish_copy(wrapped, ed_brief())
    plan["blocks"] = [wrapped[f"b{i}"] for i in range(len(blocks))]
    if not plan.get("blocks") or plan["blocks"][0].get("type") != "hero":
        plan["blocks"] = [{"type": "hero", "variant": "wordmark_photo", "wordmark": st.session_state.get("ed_label", "")}] + plan.get("blocks", [])
    if plan["blocks"][0].get("variant") not in ED_HERO_VARIANTS:
        plan["blocks"][0]["variant"] = "wordmark_photo"
    for b in plan["blocks"]:
        if b.get("type") in ED_LAYOUT_BLOCKS and b.get("layout") not in ("a", "b", "c"):
            b["layout"] = "a"
    if plan.get("pack") not in ED_PACKS:
        plan["pack"] = "noir_navy"
    plan = ed_naturalize(plan)
    return ed_arrange(plan)

ED_DESC_KEYS = {"desc", "body", "items", "closing", "sub", "line", "left_result", "right_result", "caption", "box", "lead", "structure"}

def _ed_metaphor_words(plan: dict) -> list:
    """비유어 = 모티프 단어 (「키워드」는 학습 내용어일 수 있어 제외)"""
    kit = plan.get("kit") or {}
    words = re.split(r"[·,/\s]+", str(kit.get("motif", "")))
    return [w for w in words if len(w) >= 2]

def ed_metaphor_report(plan: dict) -> dict:
    """설명·본문에 비유어가 몇 번 쓰였는지 (블록 인덱스 → 횟수)"""
    words = _ed_metaphor_words(plan)
    rep = {}
    for i, b in enumerate(plan.get("blocks") or []):
        if b.get("type") == "hero" or b.get("hidden"):
            continue
        n = 0
        def _scan(v, key=""):
            nonlocal n
            if isinstance(v, str):
                if key in ED_DESC_KEYS:
                    n += sum(v.count(w) for w in words) + len(re.findall(r"처럼|듯이|듯 ", v))
            elif isinstance(v, dict):
                for k, vv in v.items():
                    _scan(vv, k if k in ED_DESC_KEYS else key)
            elif isinstance(v, list):
                for vv in v:
                    _scan(vv, key)
        for k, v in b.items():
            if k not in ("type", "layout", "nav", "hidden") and not str(k).startswith("_"):
                _scan(v, k)
        if n:
            rep[i] = n
    return rep

def ed_naturalize(plan: dict) -> dict:
    """[v13] AI 티 제거: 비유 남발 · 예시 문장 베끼기 · 근거 없는 비율 블록 · 영문 타이틀 중복"""
    blocks = plan.get("blocks") or []
    facts = _user_facts()
    # 1) 근거 없는 비율 블록 제거
    keep = []
    for b in blocks:
        if b.get("type") == "balance" and not b.get("_needs"):
            pcts = [str((b.get(side) or {}).get("pct", "")) for side in ("left", "right")]
            nums = [re.sub(r"\D", "", p) for p in pcts if re.search(r"\d", p)]
            if not nums or not all(n and n in facts for n in nums):
                continue
        keep.append(b)
    blocks = keep
    # 2) 영문 타이틀 중복 → 뒤쪽은 비움(렌더러가 한글만 표시)
    seen = set()
    for b in blocks:
        t = str(b.get("title_en", "")).strip()
        pat = re.sub(r"\s+\S+$", "", t.lower())
        if t and pat in seen:
            b["title_en"] = ""
        elif t:
            seen.add(pat)
    plan["blocks"] = blocks
    # 3) 비유 남발·베낀 문장 → 해당 블록만 평이하게 다시 쓰기
    rep = ed_metaphor_report(plan)
    total = sum(rep.values())
    copied = {i for i, b in enumerate(blocks) if any(p in json.dumps(b, ensure_ascii=False) for p in ED_COPIED_PHRASES)}
    simile = set()
    _mw = _ed_metaphor_words(plan)
    for i, b in enumerate(blocks):
        txt = json.dumps({k: v for k, v in b.items() if k in ED_DESC_KEYS}, ensure_ascii=False)
        if re.search(r"(" + "|".join(map(re.escape, _mw or ["@@"])) + r")[^\"]{0,8}(처럼|같이|듯)", txt) or \
           re.search(r"(처럼|같이)[^\"]{0,12}(" + "|".join(map(re.escape, _mw or ["@@"])) + r")", txt):
            simile.add(i)
    targets = sorted(set([i for i, n in rep.items() if n >= 2] if total > 5 else []) | copied | simile)
    if targets and st.session_state.get("api_key"):
        sub = {f"b{i}": blocks[i] for i in targets}
        prompt = (
            f"{ed_brief()}\n\n아래 블록들의 문구가 AI가 쓴 것처럼 어색합니다. 같은 키·같은 구조로 다시 쓰세요.\n"
            f"- 설명·본문·목록(desc, body, items, line, sub, closing 등)에서 비유어({', '.join(_ed_metaphor_words(plan))})와 '~처럼/~듯이' 직유를 빼고, "
            "실제로 무엇을 배우고 어떻게 공부하는지 평이하게 쓰세요.\n"
            "- 「키워드」와 제목(title)은 유지해도 됩니다.\n"
            f"- 다음 표현은 다른 강좌의 문장이므로 쓰지 마세요: {', '.join(ED_COPIED_PHRASES)}\n\n"
            f"{json.dumps(sub, ensure_ascii=False)}\n\nJSON만 반환:")
        try:
            fixed = safe_json(call_ai(prompt, max_tokens=4000, temperature=0.6))
            for i in targets:
                nb = fixed.get(f"b{i}")
                if isinstance(nb, dict) and nb.get("type", blocks[i]["type"]) == blocks[i]["type"]:
                    nb["type"] = blocks[i]["type"]
                    for k in ("layout", "variant", "nav"):
                        if k in blocks[i]:
                            nb.setdefault(k, blocks[i][k])
                    blocks[i] = nb
        except Exception:
            pass
    plan["blocks"] = blocks
    return plan

ED_ORDER_TAIL = ["video", "lineup", "pass_box", "benefit"]

def ed_arrange(plan: dict) -> dict:
    """[v13] 순서 보정: 히어로 맨 앞, (영상) → 교재 → 구매 → 혜택은 뒤쪽으로"""
    blocks = plan.get("blocks") or []
    hero = [b for b in blocks if b.get("type") == "hero"][:1]
    body = [b for b in blocks if b.get("type") not in ED_ORDER_TAIL and b.get("type") != "hero"]
    tail = sorted([b for b in blocks if b.get("type") in ED_ORDER_TAIL], key=lambda b: ED_ORDER_TAIL.index(b["type"]))
    plan["blocks"] = hero + body + tail
    return plan

def ed_regen_block(plan: dict, idx: int, request: str) -> dict:
    b = plan["blocks"][idx]
    spec = ED_BLOCK_SPECS.get(b.get("type"), ("", "{}"))[1]
    prompt = (f"{ed_brief()}\n\n[이 페이지의 컨셉 키트]\n{json.dumps(plan.get('kit', {}), ensure_ascii=False)}\n\n"
              f"[현재 블록]\n{json.dumps({k: v for k, v in b.items() if not str(k).startswith('_') and k != 'hidden'}, ensure_ascii=False)}\n\n[요청] {request or '같은 구조로 다른 표현으로 다시 써주세요'}\n\n"
              f"같은 type의 블록 JSON 하나만 반환. 형식:\n{spec}")
    st.session_state["_last_ctx"] = _ed_inputs_text()
    nb = safe_json(call_ai(prompt, max_tokens=2500, temperature=0.9))
    nb["type"] = b.get("type")
    if b.get("type") == "hero" and nb.get("variant") not in ED_HERO_VARIANTS:
        nb["variant"] = b.get("variant", "wordmark_photo")
    nb = polish_copy({"b": nb}, ed_brief())["b"]
    nb = proofread_copy(nb, st.session_state.get("ed_label", ""))
    for k, v in nb.items():          # 검사에서 비워진 칸은 이전 문구 유지
        if v in ("", [], None) and b.get(k) and not str(k).startswith("_"):
            nb[k] = b[k]
    for k in ("_alts", "_needs", "hidden"):
        nb.pop(k, None)
    if b.get("layout") and b.get("type") in ED_LAYOUT_BLOCKS:
        nb.setdefault("layout", b["layout"])
    _nav = b.get("nav") or (re.search(r'"nav":"([^"]+)"', spec) or [None, None])[1]
    if _nav:
        nb.setdefault("nav", _nav)
    if ED_KEY_FIELDS.get(nb.get("type")):     # [v14] 핵심 문구는 후보 3개 중 고르기
        tmp = {"kit": plan.get("kit"), "blocks": list(plan["blocks"])}
        tmp["blocks"][idx] = nb
        nb = ed_copy_workshop(tmp, only_idx=idx)["blocks"][idx]
    return nb

# ══════════════════════════════════════════════════════════════════════
# [v12] 🎨 AI 이미지 생성 — 히어로 배경 · 키 비주얼 · 섹션 텍스처
#   · Gemini(Nano Banana) 또는 OpenAI(GPT Image) API 키가 있으면 빌더 안에서 바로 생성
#   · 키가 없으면 '프롬프트 복사 → Gemini/ChatGPT 앱에서 생성 → 업로드'
#   · 사람 얼굴·글자·로고는 넣지 않음 (강사 사진은 반드시 실제 사진 사용)
# ══════════════════════════════════════════════════════════════════════
IMG_SLOTS = {
    "hero_bg":    {"label": "히어로 배경",        "ar": "16:9", "size": "1536x1024",
                   "help": "히어로 전체 배경. 가운데를 비워 워드마크가 잘 보이게"},
    "key_visual": {"label": "키 비주얼 (오브제)", "ar": "1:1",  "size": "1024x1024",
                   "help": "컨셉을 상징하는 오브제 하나. 히어로·프롤로그·메시지 섹션에 사용"},
    "texture":    {"label": "섹션 텍스처",        "ar": "16:9", "size": "1536x1024",
                   "help": "추상 텍스처. 특징 섹션의 이미지 띠, 배경 등에 사용"},
}
GEMINI_IMG_MODELS = ["gemini-3.1-flash-image", "gemini-3.1-flash-image-preview"]
OPENAI_IMG_MODELS = ["gpt-image-2", "gpt-image-1.5"]
IMG_RULES = ("Absolutely no text, letters, numbers, logos or watermarks. No people, no faces, no hands. "
             "Premium editorial art direction for a Korean education brand landing page, cinematic lighting, high detail.")

def _secret(name: str) -> str:
    try:
        return st.secrets.get(name, "") or ""
    except Exception:
        return ""

def _img_to_datauri(raw: bytes, max_w: int = 1600, keep_png: bool = False) -> str:
    from PIL import Image
    import io
    im = Image.open(io.BytesIO(raw))
    has_alpha = im.mode in ("RGBA", "LA", "P")
    im = im.convert("RGBA" if (keep_png and has_alpha) else "RGB")
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    if im.mode == "RGBA":
        im.save(buf, format="PNG", optimize=True); mime = "png"
    else:
        im.save(buf, format="JPEG", quality=86); mime = "jpeg"
    return f"data:image/{mime};base64,{base64.b64encode(buf.getvalue()).decode()}"

def img_generate(provider: str, prompt: str, slot: str) -> str:
    """이미지 1장 생성 → data URI. 실패 시 이유가 담긴 예외."""
    meta = IMG_SLOTS[slot]
    errors = []
    if provider == "gemini":
        key = (st.session_state.get("gemini_key") or _secret("GEMINI_API_KEY")).strip()
        if not key:
            raise ValueError("Gemini API 키가 없습니다. (Google AI Studio → Get API key)")
        for model in GEMINI_IMG_MODELS:
            body = {"contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": meta["ar"]}}}
            for attempt in range(2):
                r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                  headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                                  json=body, timeout=180)
                if r.status_code == 400 and attempt == 0 and "imageConfig" in body["generationConfig"]:
                    body["generationConfig"].pop("imageConfig")      # 비율 옵션 미지원 모델 → 비율 없이 재시도
                    continue
                if not r.ok:
                    try: msg = r.json().get("error", {}).get("message", r.text[:160])
                    except Exception: msg = r.text[:160]
                    errors.append(f"{model}: HTTP {r.status_code} {msg}")
                    break
                for cand in r.json().get("candidates", []):
                    for part in (cand.get("content") or {}).get("parts", []):
                        inline = part.get("inlineData") or part.get("inline_data")
                        if inline and inline.get("data"):
                            return _img_to_datauri(base64.b64decode(inline["data"]), keep_png=(slot == "key_visual"))
                errors.append(f"{model}: 이미지가 응답에 없음 (안전 필터에 걸렸을 수 있어요)")
                break
    elif provider == "openai":
        key = (st.session_state.get("openai_key") or _secret("OPENAI_API_KEY")).strip()
        if not key:
            raise ValueError("OpenAI API 키가 없습니다. (platform.openai.com → API keys)")
        for model in OPENAI_IMG_MODELS:
            r = requests.post("https://api.openai.com/v1/images/generations",
                              headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                              json={"model": model, "prompt": prompt, "size": meta["size"], "quality": "medium", "n": 1},
                              timeout=240)
            if not r.ok:
                try: msg = r.json().get("error", {}).get("message", r.text[:160])
                except Exception: msg = r.text[:160]
                errors.append(f"{model}: HTTP {r.status_code} {msg}")
                continue
            d = (r.json().get("data") or [{}])[0]
            if d.get("b64_json"):
                return _img_to_datauri(base64.b64decode(d["b64_json"]), keep_png=(slot == "key_visual"))
            if d.get("url"):
                return _img_to_datauri(requests.get(d["url"], timeout=60).content)
            errors.append(f"{model}: 이미지가 응답에 없음")
    else:
        raise ValueError("이미지 생성 방식을 선택해주세요.")
    raise Exception(" / ".join(errors[-3:]) or "이미지 생성 실패")

def img_prompts_template(plan: dict) -> dict:
    kit = plan.get("kit") or {}
    pk = ED_PACKS.get(plan.get("pack"), ED_PACKS["noir_navy"])
    motif = kit.get("motif") or kit.get("concept_en") or "precision"
    concept = kit.get("concept_en", "")
    tone = f"color palette of deep {pk['dark']} shadows with restrained {pk['accent']} accent light"
    return {
        "hero_bg": (f"Wide cinematic hero background. Abstract visual metaphor of '{motif}' (concept: {concept}). "
                    f"{tone}. Strong depth, subtle haze, the center third kept dark and empty for a large title. {IMG_RULES}"),
        "key_visual": (f"One sculptural object that symbolizes '{motif}', centered, floating, studio product lighting, "
                       f"seamless dark background, {tone}, soft rim light, minimal composition, photoreal 3D render. {IMG_RULES}"),
        "texture": (f"Wide abstract texture inspired by '{motif}': fine lines, soft gradients and light grain, {tone}, "
                    f"no focal subject, even detail across the frame so it can be cropped into strips. {IMG_RULES}"),
    }

def img_prompts_auto(plan: dict) -> dict:
    """컨셉 키트로 영문 이미지 프롬프트 작성 (Groq). 실패하면 템플릿."""
    base = img_prompts_template(plan)
    if not st.session_state.get("api_key"):
        return base
    kit = plan.get("kit") or {}
    pk = ED_PACKS.get(plan.get("pack"), ED_PACKS["noir_navy"])
    prompt = (
        "You are an art director for premium Korean education landing pages (editorial, serif, cinematic).\n"
        f"Course: {st.session_state.get('ed_label','')} / subject: {st.session_state.get('ed_subject','')}\n"
        f"Concept kit: {json.dumps(kit, ensure_ascii=False)}\n"
        f"Palette: dark {pk['dark']}, accent {pk['accent']}, light {pk['alt']}\n"
        "Write three English image-generation prompts (60-90 words each) that express the concept metaphor visually:\n"
        "hero_bg = wide 16:9 cinematic background, center kept empty for a big title;\n"
        "key_visual = one symbolic object, centered, seamless dark background;\n"
        "texture = abstract wide texture that can be cropped into strips.\n"
        f"Every prompt must end with: {IMG_RULES}\n"
        'Return JSON only: {"hero_bg":"...","key_visual":"...","texture":"..."}'
    )
    try:
        d = safe_json(call_ai(prompt, max_tokens=1500, temperature=0.7))
        return {k: (str(d.get(k)).strip() if d.get(k) else base[k]) for k in IMG_SLOTS}
    except Exception:
        return base

def ed_restyle(plan: dict) -> dict:
    """AI 호출 없이 스타일 팩 · 히어로 형태 · 블록 레이아웃(a/b)을 바꿔보기"""
    plan["pack"] = _erandom.choice([k for k in ED_PACKS if k != plan.get("pack")])
    for b in plan.get("blocks") or []:
        if b.get("type") == "hero":
            b["variant"] = _erandom.choice([v for v in ED_HERO_VARIANTS if v != b.get("variant")])
        elif b.get("type") in ED_LAYOUT_BLOCKS:
            n = len(ED_LAYOUT_BLOCKS[b["type"]].split(" / "))
            b["layout"] = _erandom.choice(["a", "b", "c"][:n])
    return plan


# ── 화면 ──────────────────────────────────────────────────
_ED_DEFAULTS = {"ed_inst": "", "ed_label": "", "ed_subject": "영어", "ed_target": "고3·N수", "ed_memo": "", "ed_courses": "",
                "ed_books": "", "ed_pass_name": "", "ed_pass_inc": "", "ed_pass_orig": "", "ed_pass_price": "", "ed_pass_disc": "",
                "ed_pass_link": "", "ed_pass_note": "", "ed_benefit": "", "ed_video": "", "ed_concept": "",
                "ed_notice": "", "ed_plan": None, "ed_photo": "", "ed_books_img": [],
                "ed_imgs": {}, "ed_img_prompts": {}, "ed_img_provider": "gemini", "ed_full": True}

def _ed_img_b64(f, max_w=1400) -> str:
    from PIL import Image
    import io
    im = Image.open(f)
    im = im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    if im.mode == "RGBA":
        im.save(buf, format="PNG", optimize=True); mime = "png"
    else:
        im.save(buf, format="JPEG", quality=85); mime = "jpeg"
    return f"data:image/{mime};base64,{base64.b64encode(buf.getvalue()).decode()}"

def _ed_ctx() -> dict:
    g = st.session_state.get
    return {"label": g("ed_label") or "", "photo": g("ed_photo") or "", "books": g("ed_books_img") or [],
            "imgs": dict(g("ed_imgs") or {}),
            "video": g("ed_video") or "", "notice": g("ed_notice") or DEFAULT_NOTICE,
            "pass": {"name": g("ed_pass_name"), "includes": g("ed_pass_inc"), "orig": g("ed_pass_orig"),
                     "price": g("ed_pass_price"), "disc": g("ed_pass_disc"), "link": g("ed_pass_link"), "note": g("ed_pass_note")}}

def _ed_field_editor(b: dict, i: int):
    """블록 안의 문구를 종류에 맞는 입력칸으로 보여줌 (복잡한 목록은 JSON으로)"""
    changed = False
    alts = b.get("_alts") or {}
    for k, v in list(b.items()):
        if k in ("type", "hidden") or str(k).startswith("_"):
            continue
        key = f"edf_{i}_{k}"
        if k in alts and isinstance(v, str):
            opts = [o for o in alts[k].get("opts", []) if o != v]
            if opts:
                KEEP = "(지금 문구 유지)"
                role = ED_KEY_FIELDS.get(b.get("type"), {}).get(k, ED_FIELD_LABELS.get(k, k))
                sel = st.selectbox(f"💡 {role} — 다른 후보 {len(opts)}개 (고르면 바로 바뀜)", [KEEP] + opts, key=f"edalt_{i}_{k}",
                                   help=("디렉터 선택 이유: " + alts[k].get("why", "")) if alts[k].get("why") else None)
                if sel != KEEP:
                    b[k] = sel
                    st.session_state.pop(key, None)
                    st.session_state.pop(f"edalt_{i}_{k}", None)
                    st.rerun()
        if k == "layout" and b.get("type") in ED_LAYOUT_BLOCKS:
            labels = ED_LAYOUT_BLOCKS[b["type"]].split(" / ")
            opts = ["a", "b", "c"][:len(labels)]
            nv = st.radio("레이아웃", opts, index=opts.index(v) if v in opts else 0, horizontal=True,
                          format_func=lambda o: labels[opts.index(o)], key=key)
        elif k == "variant" and b.get("type") == "hero":
            opts = list(ED_HERO_VARIANTS)
            nv = st.selectbox("히어로 레이아웃", opts, index=opts.index(v) if v in opts else 0,
                              format_func=lambda o: ED_HERO_VARIANTS[o], key=key)
        elif isinstance(v, str):
            lab = ED_FIELD_LABELS.get(k, k)
            nv = (st.text_area(lab, v, key=key, height=80) if len(v) > 40 else st.text_input(lab, v, key=key))
        elif isinstance(v, list) and all(isinstance(t, str) for t in v):
            nv = [t for t in st.text_area(f"{ED_FIELD_LABELS.get(k, k)} (한 줄에 하나)", "\n".join(v), key=key, height=90).splitlines() if t.strip()]
        else:
            raw = st.text_area(f"{ED_FIELD_LABELS.get(k, k)} (고급 · JSON 형식)", json.dumps(v, ensure_ascii=False, indent=1), key=key, height=140)
            try:
                nv = json.loads(raw)
            except Exception:
                st.caption("⚠️ JSON 형식이 맞지 않아 이전 값을 유지합니다.")
                nv = v
        if nv != v:
            b[k] = nv
            changed = True
    return changed


def ed_copy_md(plan: dict, x: dict) -> str:
    """섹션별 문구 원고 (디자이너·검수용)"""
    kit = plan.get("kit") or {}
    lines = [f"# {x.get('label','')} — PR 페이지 문구 원고", "",
             f"- 컨셉: {kit.get('concept_en','')} / {kit.get('verb','')} / 모티프: {kit.get('motif','')}",
             f"- 키워드: {' '.join(str(k) for k in (kit.get('keywords') or []))}",
             f"- 대구: {kit.get('antithesis','')}",
             f"- 스타일 팩: {ED_PACKS.get(plan.get('pack'), {}).get('name','')}", ""]
    def _flat(v, indent=""):
        if isinstance(v, str):
            return [f"{indent}{v}"] if v.strip() else []
        if isinstance(v, dict):
            out = []
            for k2, v2 in v.items():
                sub = _flat(v2, indent + "  ")
                if sub:
                    out.append(f"{indent}- {k2}:"); out += sub
            return out
        if isinstance(v, list):
            out = []
            for it in v:
                out += _flat(it, indent + "  ")
            return out
        return []
    shown = [b for b in (plan.get("blocks") or []) if not b.get("hidden") and not _ed_is_empty(b)]
    for i, b in enumerate(shown):
        lines.append(f"## {i + 1:02d}. {ED_BLOCK_SPECS.get(b.get('type'), (b.get('type'),))[0]}")
        for k, v in b.items():
            if k in ("type", "variant", "layout", "nav", "hidden") or str(k).startswith("_"):
                continue
            body = _flat(v, "  ")
            if body:
                lines.append(f"- **{k}**"); lines += body
        lines.append("")
    p = x.get("pass") or {}
    if p.get("name"):
        lines += ["## 구매 정보 (MD 입력값)", f"- 상품명: {p.get('name')}", f"- 구성: {(p.get('includes') or '').replace(chr(10), ', ')}",
                  f"- 정가/판매가/할인: {p.get('orig','')} / {p.get('price','')} / {p.get('disc','')}", ""]
    lines += ["## 유의사항"] + [f"- {t}" for t in (x.get("notice") or "").splitlines() if t.strip()]
    return "\n".join(lines)

def ed_package_zip(plan: dict, x: dict) -> bytes:
    import io, zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("01_시안_미리보기.html", ed_build_html(plan, x, export=True, img_mode="path"))
        z.writestr("02_CMS_삽입용_코드.txt", ed_build_html(plan, x, export=True, img_mode="placeholder", fragment=True))
        z.writestr("03_문구_원고.md", ed_copy_md(plan, x))
        for uri, name, desc in _ed_img_registry(x):
            m = re.match(r"data:image/(\w+);base64,(.+)", uri or "", re.S)
            if m:
                z.writestr(f"images/{name}.{'png' if m.group(1) == 'png' else 'jpg'}", base64.b64decode(m.group(2)))
        z.writestr("00_읽어주세요.txt",
                   "[실무 적용 순서]\n"
                   "1. 01_시안_미리보기.html 을 크롬으로 열어 MD 검수 (images 폴더와 같은 위치에 있어야 이미지가 보입니다)\n"
                   "2. 03_문구_원고.md 의 가격·날짜·수치를 최종 확인\n"
                   "3. 퍼블리싱: 02_CMS_삽입용_코드.txt 를 에디터 HTML(소스) 모드에 붙여넣고,\n"
                   "   [이미지 교체 목록] 주석에 적힌 자리표시 이미지(placehold.co)를 실제 CDN 이미지 주소로 바꿉니다.\n"
                   "   - CSS는 #dm-promo-wrap 안에서만 작동하므로 사이트 상단 메뉴·푸터에 영향을 주지 않습니다.\n"
                   "   - 에디터가 <style>·<link> 태그를 지우는 경우, 퍼블리셔에게 이 파일을 그대로 전달해 주세요.\n"
                   "4. images 폴더의 AI 이미지는 '방향 시안'입니다. 최종 사용 전 디자이너 보정 및 사내 검수\n"
                   "   - 강사 사진은 반드시 실제 촬영본 사용 (AI로 인물 생성 금지)\n"
                   "5. 관리자 '강좌 특징' 영역은 빌더의 📝 강좌 특징 HTML 모드로 별도 제작\n")
    return buf.getvalue()


def _ed_clear_widgets(*prefixes):
    """블록 순서·내용이 바뀌면 입력칸 위젯 상태를 지워 새 값이 보이게"""
    prefixes = prefixes or ("edf_", "edalt_", "edrq")
    for k in [k for k in st.session_state.keys() if str(k).startswith(prefixes)]:
        del st.session_state[k]

def render_editorial_mode():
    for k, v in _ED_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v
    S = st.session_state

    with st.sidebar:
        st.markdown('<div class="sec-hdr">🔑 Groq API</div>', unsafe_allow_html=True)
        if not S.api_key:
            _k = st.text_input("API Key", type="password", placeholder="gsk_...", key="ed_api_in")
            if _k:
                S.api_key = _k
        else:
            st.caption("✓ API 키 연결됨")
        st.markdown('<div class="sec-hdr">🖼 이미지</div>', unsafe_allow_html=True)
        ph = st.file_uploader("강사 사진 (누끼 PNG 권장)", type=["png", "jpg", "jpeg", "webp"], key="ed_photo_up")
        S.ed_photo = _ed_img_b64(ph) if ph else ""
        bks = st.file_uploader("교재·키비주얼 이미지 (여러 장)", type=["png", "jpg", "jpeg", "webp"],
                               accept_multiple_files=True, key="ed_books_up")
        S.ed_books_img = [_ed_img_b64(f, 900) for f in (bks or [])]
        st.markdown('<div class="sec-hdr">🎬 OT 영상</div>', unsafe_allow_html=True)
        S.ed_video = st.text_input("유튜브 링크", S.ed_video, placeholder="https://youtu.be/...", label_visibility="collapsed")
        st.markdown('<div class="sec-hdr">💾 저장 / 불러오기</div>', unsafe_allow_html=True)
        save = {k: S[k] for k in _ED_DEFAULTS if k not in ("ed_photo", "ed_books_img")}
        st.download_button("작업 파일 저장 (.json)", json.dumps(save, ensure_ascii=False, indent=1).encode("utf-8"),
                           file_name=f"시안형_{S.ed_label or '작업'}.json", mime="application/json", use_container_width=True)
        up = st.file_uploader("작업 파일 불러오기", type=["json"], key="ed_proj_up", label_visibility="collapsed")
        if up is not None and S.get("_ed_loaded") != up.name + str(up.size):
            try:
                for k, v in json.loads(up.getvalue().decode("utf-8")).items():
                    if k in _ED_DEFAULTS:
                        S[k] = v
                S["_ed_loaded"] = up.name + str(up.size)
                st.rerun()
            except Exception as e:
                st.error(f"불러오기 실패: {e}")

    st.markdown("### ✨ 시안형 PR 페이지")
    st.caption("컨셉 단어 하나로 히어로부터 구매 박스까지 이어지는 PR 페이지를 만듭니다. 만들 때마다 구성과 스타일이 달라집니다.")
    L, R = st.columns([1, 1.6], gap="large")

    with L:
        with st.expander("① 강좌 정보", expanded=S.ed_plan is None):
            c1, c2 = st.columns(2)
            S.ed_inst = c1.text_input("강사명", S.ed_inst)
            S.ed_label = c2.text_input("강좌명 (워드마크)", S.ed_label, placeholder="예: Deviser, CONTACT")
            c3, c4 = st.columns(2)
            S.ed_subject = c3.text_input("과목", S.ed_subject)
            S.ed_target = c4.text_input("대상", S.ed_target)
            S.ed_concept = st.text_input("컨셉 단어 (선택)", S.ed_concept,
                                         placeholder="비우면 AI가 강좌명에서 뽑음 · 예: 설계, 접점, 밸런스")
            S.ed_memo = st.text_area("기획 메모 · 원고", S.ed_memo, height=130,
                                     placeholder="강좌의 기획 의도, 차별점, 하고 싶은 말을 자유롭게. 비율·회차 같은 숫자는 여기 적은 것만 페이지에 들어갑니다.")
            S.ed_courses = st.text_area("강좌 라인업 (선택, 한 줄에 하나)", S.ed_courses, height=70,
                                        placeholder="The GUIDANCE (이론)\nCONTACT Blue (N제)\nBLITZ (실모)")
            S.ed_books = st.text_area("교재 정보 (선택)", S.ed_books, height=70,
                                      placeholder="통합과학1: 01 과학의 기초, 02 물질과 규칙성 …")
        with st.expander("② 구매 · 혜택 (입력값 그대로 표시)", expanded=False):
            S.ed_pass_name = st.text_input("상품명", S.ed_pass_name, placeholder="예: 홍준용 Deviser 교재패스 (총 7권)")
            S.ed_pass_inc = st.text_area("구성 (한 줄에 하나)", S.ed_pass_inc, height=80)
            c5, c6, c7 = st.columns(3)
            S.ed_pass_orig = c5.text_input("정가", S.ed_pass_orig, placeholder="169,000원")
            S.ed_pass_price = c6.text_input("판매가", S.ed_pass_price, placeholder="152,100원")
            S.ed_pass_disc = c7.text_input("할인 표시", S.ed_pass_disc, placeholder="10%")
            S.ed_pass_link = st.text_input("구매 링크", S.ed_pass_link)
            S.ed_pass_note = st.text_input("구매 안내 문구", S.ed_pass_note, placeholder="※ 교재패스 구매 후 교재 신청까지 완료해야 배송됩니다.")
            S.ed_benefit = st.text_area("혜택·이벤트 (기간·대상·내용)", S.ed_benefit, height=70)
            S.ed_notice = st.text_area("유의사항 (한 줄에 하나)", S.ed_notice or DEFAULT_NOTICE, height=90)

        S.ed_full = st.checkbox("모든 섹션을 먼저 펼쳐 놓고, 순서·표시는 내가 고르기", value=S.ed_full, key="ed_full_ck",
                                help="켜면 블록 라이브러리의 섹션을 전부 작성해 둡니다. 아래 '③ 순서 · 표시'에서 ▲▼로 순서를 바꾸고 👁로 뺄 섹션을 숨기세요. "
                                     "끄면 AI가 6~9개를 골라 구성합니다.")
        b1, b2 = st.columns(2)
        gen = b1.button("✨ 페이지 만들기" if S.ed_plan is None else "🔀 구성 다시 짜기", type="primary", use_container_width=True)
        restyle = b2.button("🎨 스타일만 바꾸기", use_container_width=True, disabled=S.ed_plan is None)
        if gen:
            if not S.ed_label.strip():
                st.warning("강좌명을 입력해주세요.")
            elif not S.api_key:
                st.warning("사이드바에 API 키를 입력해주세요.")
            else:
                avoid = ""
                if S.ed_plan:
                    avoid = "이전 구성: " + " → ".join(b.get("type", "") for b in S.ed_plan.get("blocks", [])) + \
                            f" / 이전 컨셉: {S.ed_plan.get('kit', {}).get('verb', '')}"
                with st.spinner("컨셉을 정하고 섹션을 쓰는 중... 핵심 문구는 후보 3개씩 써서 고릅니다 (1~2분)"):
                    try:
                        S.ed_plan = ed_generate_full(avoid) if S.ed_full else ed_generate_plan(avoid)
                        _ed_clear_widgets()
                        st.rerun()
                    except Exception as e:
                        st.error(f"생성 실패: {e}")
        if restyle and S.ed_plan:
            S.ed_plan = ed_restyle(S.ed_plan)
            _ed_clear_widgets("edf_")
            st.rerun()

        plan = S.ed_plan
        if plan:
            _model_quality_note()
            kit = plan.get("kit") or {}
            st.markdown(f"**컨셉 키트** · {kit.get('concept_en','')} / {kit.get('verb','')} / "
                        f"{' '.join(str(k) for k in (kit.get('keywords') or []))}")
            if kit.get("antithesis"):
                st.caption(f"대구: {kit['antithesis']}")
            pk_keys = list(ED_PACKS)
            newpk = st.selectbox("스타일 팩", pk_keys, index=pk_keys.index(plan.get("pack", "noir_navy")),
                                 format_func=lambda k: ED_PACKS[k]["name"])
            if newpk != plan.get("pack"):
                plan["pack"] = newpk
                st.rerun()
            _hopts = ["팩 기본", "고딕 (Pretendard)", "명조 (Noto Serif KR)"]
            _hcur = {"sans": 1, "serif": 2}.get(plan.get("head"), 0)
            _hsel = st.radio("한글 제목 서체", _hopts, index=_hcur, horizontal=True, key="ed_head_rd",
                             help="본문·버튼은 항상 Pretendard입니다. 명조는 큰 제목에만 들어가요.")
            _hval = {1: "sans", 2: "serif"}.get(_hopts.index(_hsel))
            if _hval != plan.get("head"):
                plan["head"] = _hval
                st.rerun()
            deco = st.checkbox("섹션 장식 (아웃라인 영문 · 컨셉 모티프 그래픽)", value=plan.get("deco", True), key="ed_deco_ck")
            if deco != plan.get("deco", True):
                plan["deco"] = deco
                st.rerun()
            _mrep = ed_metaphor_report(plan)
            if sum(_mrep.values()) > 5:
                st.warning(f"설명 문구에 비유가 {sum(_mrep.values())}번 쓰였어요. AI 티가 날 수 있으니 해당 블록을 '이 블록만 다시 쓰기'로 평이하게 바꿔보세요.")
            # ── [v12] AI 이미지 ─────────────────────────────
            with st.expander("🎨 AI 이미지 — 히어로 배경 · 키 비주얼 · 텍스처", expanded=not S.ed_imgs):
                st.caption("컨셉에 맞는 이미지를 만들어 히어로·섹션에 자동으로 넣습니다. 사람 얼굴·글자·로고는 넣지 않아요 (강사 사진은 실제 사진을 사이드바에 올려주세요).")
                prov_opts = {"gemini": "Gemini (Nano Banana)", "openai": "OpenAI (GPT Image)", "manual": "직접 만들기 (프롬프트 복사 → 앱에서 생성 → 업로드)"}
                S.ed_img_provider = st.radio("생성 방식", list(prov_opts), index=list(prov_opts).index(S.ed_img_provider),
                                             format_func=lambda k: prov_opts[k], key="ed_prov")
                if S.ed_img_provider == "gemini" and not _secret("GEMINI_API_KEY"):
                    S["gemini_key"] = st.text_input("Gemini API 키", S.get("gemini_key", ""), type="password",
                                                    help="Google AI Studio(aistudio.google.com) → Get API key")
                if S.ed_img_provider == "openai" and not _secret("OPENAI_API_KEY"):
                    S["openai_key"] = st.text_input("OpenAI API 키", S.get("openai_key", ""), type="password",
                                                    help="platform.openai.com → API keys (결제 등록 필요)")
                if st.button("✍️ 컨셉으로 이미지 프롬프트 자동 작성", use_container_width=True):
                    with st.spinner("아트 디렉션 프롬프트 작성 중..."):
                        S.ed_img_prompts = img_prompts_auto(plan)
                        for k in IMG_SLOTS:
                            S.pop(f"ed_ip_{k}", None)
                        st.rerun()
                if not S.ed_img_prompts:
                    S.ed_img_prompts = img_prompts_template(plan)
                gen_all = (S.ed_img_provider != "manual") and st.button("⚡ 3장 한 번에 생성", type="primary", use_container_width=True)
                for slot, meta in IMG_SLOTS.items():
                    st.markdown(f"**{meta['label']}** · {meta['ar']}  \n<small>{meta['help']}</small>", unsafe_allow_html=True)
                    S.ed_img_prompts[slot] = st.text_area("프롬프트", S.ed_img_prompts.get(slot, ""), height=90,
                                                          key=f"ed_ip_{slot}", label_visibility="collapsed")
                    c_a, c_b = st.columns([1, 1])
                    if S.ed_img_provider != "manual":
                        do = c_a.button("생성", key=f"ed_gen_{slot}", use_container_width=True)
                    else:
                        do = False
                        c_a.caption("위 프롬프트를 복사해 Gemini·ChatGPT 앱에 붙여넣고, 만든 이미지를 오른쪽에 올리세요.")
                    upf = c_b.file_uploader("업로드", type=["png", "jpg", "jpeg", "webp"], key=f"ed_up_{slot}",
                                            label_visibility="collapsed")
                    if upf is not None and S.get(f"_ed_up_sig_{slot}") != upf.name + str(upf.size):
                        S.ed_imgs[slot] = _img_to_datauri(upf.getvalue(), keep_png=(slot == "key_visual"))
                        S[f"_ed_up_sig_{slot}"] = upf.name + str(upf.size)
                    if do or gen_all:
                        with st.spinner(f"{meta['label']} 생성 중... (20~60초)"):
                            try:
                                S.ed_imgs[slot] = img_generate(S.ed_img_provider, S.ed_img_prompts[slot], slot)
                            except Exception as e:
                                st.error(f"{meta['label']} 실패: {e}")
                    if S.ed_imgs.get(slot):
                        st.image(S.ed_imgs[slot], use_container_width=True)
                        if st.button("이 이미지 빼기", key=f"ed_rm_{slot}"):
                            S.ed_imgs.pop(slot, None)
                            st.rerun()
                    st.markdown("---")

            # ── [v14] ③ 순서 · 표시 — 한눈에 보고 ▲▼👁 로 고르기 ─────────
            st.markdown("**③ 순서 · 표시** — ▲▼ 순서 바꾸기 · 👁 페이지에 넣기/빼기 · 🗑 목록에서 삭제")
            st.caption("숨긴 섹션도 문구는 남아 있어서 언제든 다시 켤 수 있어요. 미리보기에는 켜진 섹션만 나옵니다.")
            nb_ = len(plan["blocks"])
            for i, b in enumerate(list(plan["blocks"])):
                label = ED_BLOCK_SPECS.get(b.get("type"), (b.get("type"),))[0]
                hid = bool(b.get("hidden"))
                empty = _ed_is_empty(b) and b.get("type") not in ("hero", "pass_box", "video")
                note = f" · ⚠️ {b['_needs']} 필요" if b.get("_needs") and empty else (" · 문구 없음" if empty else "")
                r0, r1, r2, r3, r4 = st.columns([5.2, .8, .8, .9, .8])
                r0.markdown(f"<div style='padding-top:6px;font-size:14px;{'color:#9aa3ad;text-decoration:line-through' if hid else ''}'>"
                            f"<b>{i + 1:02d}</b>&nbsp; {_ehtml.escape(label.split(' (')[0])}<span style='color:#c27a00;font-size:12px'>{_ehtml.escape(note)}</span></div>",
                            unsafe_allow_html=True)
                if r1.button("▲", key=f"edup{i}", disabled=i <= 1, use_container_width=True):
                    plan["blocks"][i - 1], plan["blocks"][i] = plan["blocks"][i], plan["blocks"][i - 1]
                    _ed_clear_widgets(); st.rerun()
                if r2.button("▼", key=f"eddn{i}", disabled=i == 0 or i >= nb_ - 1, use_container_width=True):
                    plan["blocks"][i + 1], plan["blocks"][i] = plan["blocks"][i], plan["blocks"][i + 1]
                    _ed_clear_widgets(); st.rerun()
                if r3.button("🙈" if not hid else "👁", key=f"edhide{i}", disabled=i == 0, use_container_width=True,
                             help="페이지에서 빼기" if not hid else "페이지에 넣기"):
                    b["hidden"] = not hid
                    st.rerun()
                if r4.button("🗑", key=f"eddel{i}", disabled=i == 0, use_container_width=True, help="목록에서 삭제"):
                    plan["blocks"].pop(i)
                    _ed_clear_widgets(); st.rerun()
            w1, w2 = st.columns(2)
            if w1.button("💡 핵심 문구 다시 고르기 (후보 3개씩)", use_container_width=True,
                         help="켜진 섹션의 히어로·제목·선언 문구를 각각 3가지 각도로 다시 써서 가장 좋은 것으로 바꿉니다."):
                with st.spinner("문구마다 후보 3개를 쓰고 고르는 중..."):
                    S.ed_plan = ed_copy_workshop(plan)
                    _ed_clear_widgets(); st.rerun()
            if w2.button("👁 숨긴 섹션 모두 켜기", use_container_width=True):
                for b in plan["blocks"]:
                    if not (_ed_is_empty(b) and b.get("type") not in ("hero", "pass_box", "video")):
                        b["hidden"] = False
                st.rerun()

            st.markdown("**④ 문구 편집** — 💡 후보 바꾸기 · 직접 수정 · 이 블록만 다시 쓰기")
            _needs_now = ed_block_needs()
            waiting = [(i, b) for i, b in enumerate(plan["blocks"]) if b.get("_needs") and _ed_is_empty(b)]
            for i, b in enumerate(list(plan["blocks"])):
                if b.get("_needs") and _ed_is_empty(b):
                    continue          # 아래 '정보가 필요한 섹션'에 모아서 보여줌
                label = ED_BLOCK_SPECS.get(b.get("type"), (b.get("type"),))[0]
                with st.expander(f"{i + 1:02d}. {label}{'  (숨김)' if b.get('hidden') else ''}", expanded=False):
                    if _ed_field_editor(b, i):
                        pass
                    rq = st.text_input("이 블록 다시 쓰기 요청 (선택)", key=f"edrq{i}", placeholder="예: 더 짧게 / 키워드를 '각도'로")
                    if st.button("✍️ 이 블록만 다시 쓰기", key=f"edrg{i}", use_container_width=True):
                        with st.spinner("다시 쓰는 중... (후보 3개 중 고르기 포함)"):
                            try:
                                plan["blocks"][i] = ed_regen_block(plan, i, rq or ("이 블록을 새로 작성" if _ed_is_empty(b) else ""))
                                _ed_clear_widgets(f"edf_{i}_", f"edalt_{i}_")
                                st.rerun()
                            except Exception as e:
                                st.error(f"실패: {e}")
            if waiting:
                with st.expander(f"⚠️ 정보가 더 있어야 쓸 수 있는 섹션 {len(waiting)}개 — 이 강좌에 해당 없으면 그냥 두세요", expanded=False):
                    st.caption("내용을 지어내지 않도록, 필요한 정보가 입력될 때까지 비워 둔 섹션이에요. 숨김 상태라 페이지에는 나오지 않습니다. "
                               "정보를 적은 뒤 '✍️ 채우기'를 누르면 문구가 써지고 페이지에 켜져요.")
                    for i, b in waiting:
                        label = ED_BLOCK_SPECS.get(b.get("type"), (b.get("type"),))[0].split(" (")[0]
                        miss = _needs_now.get(b.get("type"), "")
                        cA, cB = st.columns([3, 1])
                        cA.markdown(f"**{i + 1:02d}. {label}**  \n<small>{'✅ 정보 입력됨 — 채우기를 누르세요' if not miss else ED_NEEDS_HELP.get(b.get('type'), b['_needs'])}</small>",
                                    unsafe_allow_html=True)
                        if cB.button("✍️ 채우기", key=f"edfill{i}", use_container_width=True, disabled=bool(miss),
                                     help="필요한 정보를 먼저 입력해야 눌러져요" if miss else None):
                            with st.spinner("작성 중..."):
                                try:
                                    plan["blocks"][i] = ed_regen_block(plan, i, "이 블록을 새로 작성")
                                    _ed_clear_widgets(f"edf_{i}_", f"edalt_{i}_")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"실패: {e}")
            add_opts = [t for t in ED_BLOCK_SPECS if t != "hero"]
            a1, a2 = st.columns([2, 1])
            add_t = a1.selectbox("블록 추가", add_opts, format_func=lambda t: ED_BLOCK_SPECS[t][0], label_visibility="collapsed")
            if a2.button("➕ 추가", use_container_width=True):
                with st.spinner("새 블록 작성 중..."):
                    try:
                        plan["blocks"].append({"type": add_t})
                        plan["blocks"][-1] = ed_regen_block(plan, len(plan["blocks"]) - 1, "이 블록을 새로 작성")
                    except Exception as e:
                        plan["blocks"].pop()
                        st.error(f"실패: {e}")
                    st.rerun()

    with R:
        if not S.ed_plan:
            st.info("왼쪽에 강좌 정보를 넣고 '✨ 페이지 만들기'를 누르면 여기에 시안이 나타납니다.\n\n"
                    "· 강사 사진(누끼)과 교재 이미지를 사이드바에 올리면 히어로·교재 섹션에 들어갑니다.\n"
                    "· 가격·혜택·비율 같은 숫자는 입력한 값만 쓰입니다.")
            return
        html_out = ed_build_html(S.ed_plan, _ed_ctx())
        d1, d2, d3, d4 = st.columns([1.15, 1.25, 1.2, .9])
        _ctx = _ed_ctx()
        d1.download_button("📋 CMS 삽입용 코드", ed_build_html(S.ed_plan, _ctx, export=True, img_mode="placeholder", fragment=True).encode("utf-8"),
                           file_name=f"{S.ed_label or 'PR'}_CMS삽입용.txt", mime="text/plain", type="primary", use_container_width=True,
                           help="<html>·<body> 없이 본문 코드만. CSS는 #dm-promo-wrap 안에서만 작동하고, 이미지는 자리표시(placehold.co) + 교체 주석으로 들어가 용량이 가볍습니다.")
        d2.download_button("📦 실무 전달 패키지", ed_package_zip(S.ed_plan, _ctx),
                           file_name=f"{S.ed_label or 'PR'}_전달패키지.zip", mime="application/zip", use_container_width=True,
                           help="미리보기 HTML(images 폴더 경로) + CMS 코드 + 이미지 원본 + 문구 원고 + 퍼블리싱 안내")
        d3.download_button("⬇️ 미리보기 HTML", ed_build_html(S.ed_plan, _ctx, export=True).encode("utf-8"),
                           file_name=f"{S.ed_label or 'PR'}_미리보기.html", mime="text/html", use_container_width=True,
                           help="이미지까지 파일 하나에 들어 있어 용량이 큽니다. 카톡·메일로 시안 공유할 때만 쓰세요.")
        vw = d4.radio("화면", ["PC", "모바일"], horizontal=True, label_visibility="collapsed", key="ed_vw")
        if hasattr(st, "iframe"):
            st.iframe(html_out, height=1100, width=390 if vw == "모바일" else "stretch")
        else:
            import streamlit.components.v1 as components
            components.html(html_out, height=1100, width=390 if vw == "모바일" else None, scrolling=True)


# ── [v10] 작업 모드 선택 ───────────────────────────────────
APP_MODE = st.sidebar.radio("작업 모드", ["✨ 시안형 PR 페이지", "🖼 PR 페이지 빌더 (기존)", "📝 강좌 특징 HTML (관리자용)"], key="app_mode")
st.sidebar.selectbox("Groq 요금제", ["무료 (분당 8천 토큰)", "Developer (카드 등록 · 사용한 만큼 결제)"], key="groq_tier",
                     help="console.groq.com → Settings → Billing 에서 카드를 등록했다면 Developer를 고르세요. "
                          "무료는 한 번에 쓸 수 있는 양이 작아서, 문구를 나눠 쓰고 한도에 걸리면 잠시 기다립니다.")
if APP_MODE.startswith("📝"):
    render_feature_mode()
    st.stop()
if APP_MODE.startswith("✨"):
    render_editorial_mode()
    st.stop()

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
        st.markdown("**🎬 OT 영상 YouTube 링크**")
        st.caption("일반 유튜브 주소(youtu.be/…, watch?v=…)를 그대로 붙여도 됩니다")
        yt_key = "yt_url_input"
        cur_yt = (st.session_state.custom_copy or {}).get("videoUrl","") if st.session_state.custom_copy else ""
        yt_in = st.text_input("YouTube embed URL", value=cur_yt,
                              placeholder="https://youtu.be/...",
                              label_visibility="collapsed", key=yt_key)
        if yt_in and yt_in != cur_yt:
            if st.session_state.custom_copy is None:
                st.session_state.custom_copy = {}
            st.session_state.custom_copy["videoUrl"] = yt_in
            st.rerun()

    # [v8] 히어로 키비주얼 (교재 표지·누끼 PNG) — 실제 PR 페이지처럼 오른쪽에 크게 배치
    st.markdown("**📘 히어로 키비주얼 (교재 표지·누끼 이미지)**")
    st.caption("배경이 투명한 PNG를 올리면 히어로가 좌우 분할 레이아웃으로 바뀝니다")
    kv_file = st.file_uploader("키비주얼", type=["png", "jpg", "jpeg", "webp"],
                               label_visibility="collapsed", key="kv_uploader")
    if kv_file is None:
        if st.session_state.get("kv_img_b64"):
            st.session_state.kv_img_b64 = ""
            st.rerun()
    else:
        from PIL import Image
        import io
        _kv = Image.open(kv_file)
        _kv = _kv.convert("RGBA") if _kv.mode in ("RGBA", "LA", "P") else _kv.convert("RGB")
        if _kv.width > 1400:
            _kv = _kv.resize((1400, int(_kv.height * 1400 / _kv.width)), Image.LANCZOS)
        _buf = io.BytesIO()
        if _kv.mode == "RGBA":
            _kv.save(_buf, format="PNG", optimize=True); _mime = "png"
        else:
            _kv.save(_buf, format="JPEG", quality=85); _mime = "jpeg"
        _new_kv = f"data:image/{_mime};base64,{base64.b64encode(_buf.getvalue()).decode()}"
        if st.session_state.get("kv_img_b64") != _new_kv:
            st.session_state.kv_img_b64 = _new_kv
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
                   placeholder="강좌명 (예: 2028 KISS LOGIC)", label_visibility="collapsed")

    # ✅ 브랜드명 바뀌면 생성된 문구도 초기화 (이전 강좌 내용 방지)
    if pl != st.session_state.purpose_label:
        st.session_state.purpose_label = pl
        st.session_state.custom_copy = None  # 이전 문구 초기화
        st.rerun()
    mt = st.text_input("핵심 메타포 (선택)", value=st.session_state.get("metaphor", ""),
                       placeholder="예: Surfing, Racing, 등대, 해부학",
                       help="기획안 전체를 관통하는 비유적 표현을 입력하면 카피와 시각적 디렉션에 반영됩니다.")
    st.session_state.metaphor = mt

    # [v8] 기획 앵글 — 랜덤 문구 룰렛 대신 MD가 구조를 고름
    angle_opts = list(PAGE_ANGLES.keys())
    if st.session_state.get("page_angle") not in angle_opts:
        st.session_state.page_angle = angle_opts[0]
    st.session_state.page_angle = st.selectbox("기획 앵글", angle_opts,
        index=angle_opts.index(st.session_state.page_angle),
        help="페이지 전체의 설득 구조를 정합니다. '자동'이면 AI가 강좌 성격에 맞게 고릅니다.")

    # [v8] 기준 수능 · 시즌 — 날짜는 코드가 계산하고 AI는 지어내지 않음
    st.markdown('<div class="sec-hdr">🗓 기준 수능 · 시즌</div>', unsafe_allow_html=True)
    _auto_year = default_target_year()
    _years = sorted(set(list(SUNEUNG_SCHEDULE.keys()) + [_auto_year, _auto_year + 1]))
    if not st.session_state.get("target_year"):
        st.session_state.target_year = _auto_year
    def _yr_label(y):
        ex, est = exam_date_for(y)
        return f"{y}학년도 ({ex.year}.{ex.month:02d}.{ex.day:02d}{' 추정' if est else ''})"
    st.session_state.target_year = st.selectbox("기준 수능", _years,
        index=_years.index(st.session_state.target_year) if st.session_state.target_year in _years else 0,
        format_func=_yr_label, label_visibility="collapsed")
    _ss = get_season()
    st.caption(f"오늘 {_ss['today'].month}/{_ss['today'].day} 기준 → **{_ss['label']}** · 수능까지 {_ss['days']}일")
    if _ss["dday_possible"]:
        st.session_state.allow_dday = st.checkbox(f"문구에 D-day 숫자 사용 (D-{_ss['days']})",
                                                  value=st.session_state.get("allow_dday", False))
    else:
        st.session_state.allow_dday = False
        st.caption("D-day 숫자는 수능 100일 이내 + 공식 일정일 때만 켤 수 있습니다.")

    if st.session_state.purpose_type == "이벤트":
        st.session_state.event_info = st.text_area("이벤트 일정·조건 (AI가 이 값만 사용)",
            value=st.session_state.get("event_info", ""), height=80,
            placeholder="예: 기간 2026.12.01(화)~12.21(월) / 대상 KISSAVE 수강생 / 발표 12.28(월) 공지사항 / 경품 스타벅스 30명")

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

    # [v8] 유의사항 · 표시 옵션
    with st.expander("📄 유의사항 · 표시 옵션", expanded=False):
        st.session_state.notice_text = st.text_area("유의사항 (한 줄에 한 항목)",
            value=st.session_state.get("notice_text") or DEFAULT_NOTICE, height=140)
        st.session_state.fx_on = st.checkbox("배경 효과 사용 (파티클·글리치·필름 그레인)",
            value=st.session_state.get("fx_on", False),
            help="실무 페이지에서는 끄는 것을 권장합니다. 텍스트 가독성과 로딩 속도가 좋아집니다.")

# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════
# [v11] 섹션은 항상 정해진 흐름대로 정렬 (나중에 추가한 섹션이 유의사항 뒤에 붙던 문제)
SECTION_CANON = ["banner", "fest_hero", "why", "intro", "course_intro", "video", "curriculum", "target",
                 "instructor_philosophy", "reviews", "textbook_sale", "event_overview", "event_benefits",
                 "event_deadline", "fest_lineup", "fest_benefits", "faq", "custom_section", "cta", "fest_cta", "notice"]
ordered = sorted([s for s in st.session_state.active_sections if s in SECTION_CANON], key=SECTION_CANON.index)
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
        "신규 커리큘럼": "예: 2028 신규 런칭. 독해 논리 기본서. 개념→기출→적용 4단계, 노베이스~3등급 대상. 교재 2권 구성. 문장을 '번역'하던 습관을 '논리'로 바꾸는 게 핵심.",
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
                "신규 커리큘럼": ["banner","intro","why","curriculum","target","reviews","faq","cta","video"],
                "이벤트":       ["banner","event_overview","event_benefits","event_deadline","reviews","cta"],
                "기획전":       ["fest_hero","fest_lineup","fest_benefits","fest_cta"],
            }
            covered     = set(COPY_COVERS.get(ptype, []))
            NO_AI = {"custom_section", "notice", "course_intro", "textbook_sale", "instructor_philosophy"}  # 입력 기반/AI 불필요
            extra_secs  = [s for s in active if s not in covered and s not in NO_AI]
            total_steps = 1 + len(extra_secs)

            prog   = st.progress(0)
            status = st.empty()

            try:
                # 1단계: gen_copy로 메인 문구 생성 (톤+맥락 반영)
                status.info(f"✍️ 전체 문구 생성 중... (1/{total_steps})")
                st.session_state["_last_ctx"] = ctx
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
        if st.session_state.get("_last_model"):
            _model_quality_note()
            if st.session_state.get("_last_model_errors"):
                with st.expander("앞 순위 모델이 실패한 이유", expanded=False):
                    for _e in st.session_state["_last_model_errors"]:
                        st.caption(_e)
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
    regen_secs = [s for s in ordered if s in SEC_LABELS and s not in ('custom_section', 'notice')]
    if regen_secs and st.session_state.api_key:
        # [v12] 버튼 4열 → 글자가 잘리던 문제. 섹션 선택 + 버튼 1개 방식으로 변경
        rc1, rc2 = st.columns([3, 2])
        sid = rc1.selectbox("다시 쓸 섹션", regen_secs, format_func=lambda x: SEC_LABELS.get(x, x),
                            label_visibility="collapsed", key="regen_pick")
        if rc2.button("↺ 다시 쓰기", key="regen_go", use_container_width=True):
            label = SEC_SHORT.get(sid, sid)
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
                    ("text_input","상단 라벨","bannerSub"),
                    ("text_input","킥커 (워드마크 위 한 줄)","bannerKicker"),
                    ("text_input","워드마크 (강좌명)","bannerTitle"),
                    ("text_area","설명","bannerLead"),
                    ("text_input","버튼 텍스트","ctaCopy"),
                    ("text_input","영문 슬로건","brandTagline"),
                ]),
                ("💡 문제 제기", [
                    ("text_input","eyebrow","whyEyebrow"),
                    ("text_input","헤드라인","whyTitle"),
                    ("text_input","서브카피","whySub"),
                ]),
                ("📖 강좌의 정체", [
                    ("text_input","eyebrow","introEyebrow"),
                    ("text_input","선언 문장","introTitle"),
                    ("text_area","설명","introDesc"),
                    ("text_input","한 줄 포지션","introBio"),
                ]),
                ("📚 커리큘럼", [
                    ("text_input","헤드라인","curriculumTitle"),
                    ("text_input","서브카피","curriculumSub"),
                ]),
                ("📣 CTA", [
                    ("text_input","헤드라인","ctaTitle"),
                    ("text_input","서브카피","ctaSub"),
                    ("text_input","버튼 텍스트","ctaCopy"),
                    ("text_input","라벨","ctaBadge"),
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

        st.caption("💡 헤드라인에서 [[단어]]처럼 감싸면 그 단어만 포인트 컬러로 강조됩니다.")
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
        # [v8] 수강평은 반드시 실제 후기로 교체 (AI 예시 후기를 그대로 게시하지 않도록)
        with st.expander("⭐ 수강평 (실제 후기로 교체)", expanded=bool(cp.get("_reviews_sample"))):
            st.caption("한 줄에 하나씩 `후기 내용 | 이름(마스킹) | 뱃지` 형식으로 붙여넣으세요.")
            cur_rv = "\n".join(" | ".join(str(x) for x in (list(r) + ["", ""])[:3])
                                for r in (cp.get("reviews") or []) if isinstance(r, (list, tuple)))
            new_rv = st.text_area("수강평", value=cur_rv, height=140, label_visibility="collapsed", key="ed_reviews")
            if st.button("✓ 실제 후기로 적용", key="apply_reviews"):
                rows = []
                for line in new_rv.splitlines():
                    if line.strip():
                        p = [x.strip() for x in line.split("|")] + ["", ""]
                        rows.append(p[:3])
                st.session_state.custom_copy["reviews"] = rows
                st.session_state.custom_copy["_reviews_sample"] = False
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
    # SB 시트 출력
    st.markdown("### 📋 SB 시트 출력")
    if st.session_state.custom_copy and ordered:
        if st.button("📋 SB 시트 생성", use_container_width=True, key="gen_sb_sheet"):
            sb_md = generate_sb_sheet(st.session_state.custom_copy, ordered)
            st.session_state["_sb_sheet"] = sb_md

        if st.session_state.get("_sb_sheet"):
            st.download_button(
                "📥 SB 마크다운 다운로드",
                data=st.session_state["_sb_sheet"].encode("utf-8"),
                file_name=f"SB_{st.session_state.purpose_label or '페이지'}.md",
                mime="text/markdown",
                use_container_width=True,
                key="dl_sb"
            )
            with st.expander("미리보기", expanded=False):
                st.markdown(st.session_state["_sb_sheet"])
    else:
        st.caption("AI 문구 생성 후 활성화됩니다")

    st.divider()
    
    st.markdown("### 📥 HTML 내보내기")
    cn = (st.session_state.custom_theme.get("name","custom")
          if st.session_state.concept=="custom" and st.session_state.custom_theme
          else st.session_state.concept)
    st.download_button(
        "📥 HTML 파일 다운로드",
        data=build_html(ordered, exporting=True).encode("utf-8"),
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
    # [v8] Streamlit 최신 버전은 components.html이 폐기 예정 → st.iframe 우선 사용
    if hasattr(st, "iframe"):
        st.iframe(final_html, height=preview_height, width=preview_width or "stretch")
    else:
        import streamlit.components.v1 as components
        components.html(final_html, height=preview_height, width=preview_width, scrolling=True)
