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
}
for _k, _v in _D.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

if not st.session_state.api_key:
    try:
        st.session_state.api_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass

# ══════════════════════════════════════════════════════
# 상수
# ══════════════════════════════════════════════════════
GROQ_URL    = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama3-70b-8192", "mixtral-8x7b-32768"]

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
        "vars":"--c1:#AAFF00;--c2:#CCFF44;--c3:#224400;--c4:#030703;--bg:#030703;--bg2:#060E06;--bg3:#0A1A0A;--text:#F0FFF0;--t70:rgba(240,255,240,.7);--t45:rgba(240,255,240,.45);--bd:rgba(170,255,0,.18);--fh:'Space Grotesk','Noto Sans KR',sans-serif;--fb:'Space Grotesk','Noto Sans KR',sans-serif;--r:0px;--r-btn:0px;",
        "extra_css":".st{letter-spacing:.02em} .card{border-color:rgba(170,255,0,.15)!important} .btn-p{color:#030703!important}",
        "cta":"linear-gradient(135deg,#030703,#224400 40%,#AAFF00)","heroStyle":"typographic",
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
        "vars":"--c1:#F59E0B;--c2:#FCD34D;--c3:#7A4A00;--c4:#080400;--bg:#080400;--bg2:#0E0800;--bg3:#160D00;--text:#FFF8E8;--t70:rgba(255,248,232,.7);--t45:rgba(255,248,232,.45);--bd:rgba(245,158,11,.18);--fh:'Playfair Display','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:4px;--r-btn:4px;",
        "extra_css":".st{font-style:italic}",
        "cta":"linear-gradient(135deg,#080400,#7A4A00 50%,#F59E0B)","heroStyle":"immersive",
        "particle":"gold"},
}

PURPOSE_SECTIONS = {
    "신규 커리큘럼": ["banner","intro","why","curriculum","target","reviews","faq","cta"],
    "이벤트":       ["banner","event_overview","event_benefits","event_deadline","reviews","cta"],
    "기획전":       ["fest_hero","fest_lineup","fest_benefits","fest_cta"],
}
PURPOSE_HINTS = {
    "신규 커리큘럼": "📚 강사 전문성·신뢰감 강조 — 인셉션, 앰버, 코스모스 추천",
    "이벤트":       "🎉 기간 한정·긴박감·혜택 강조 — 시네마틱, 에시드, 스타디움 추천",
    "기획전":       "🏆 강사 라인업·통합 혜택 강조 — 브루탈, 골드 럭셔리, 코스모스 추천",
}
SEC_LABELS = {
    "banner":"🏠 메인 배너","intro":"👤 강사 소개","why":"💡 필요한 이유",
    "curriculum":"📚 커리큘럼","target":"🎯 수강 대상","reviews":"⭐ 수강평",
    "faq":"❓ FAQ","cta":"📣 수강신청",
    "event_overview":"📅 이벤트 개요","event_benefits":"🎁 이벤트 혜택",
    "event_deadline":"⏰ 마감 안내",
    "fest_hero":"🏆 기획전 히어로","fest_lineup":"👥 강사 라인업",
    "fest_benefits":"🎁 기획전 혜택","fest_cta":"📣 기획전 CTA",
    "custom_section":"✏️ 기타 섹션",
}
RANDOM_SEEDS = [
    {"mood":"사이버펑크 보라 네온사인 비오는 다크 도시","layout":"brutal","font":"display","particle":"none"},
    {"mood":"고대 이집트 황금 신전 사막 모래 오벨리스크","layout":"editorial","font":"serif","particle":"gold"},
    {"mood":"관중이 가득찬 야구장 밤 전광판 붉은빛 함성","layout":"brutal","font":"display","particle":"none"},
    {"mood":"수험생 새벽 4시 형광등 책상 집중과 고요 먹빛","layout":"minimal","font":"mono","particle":"none"},
    {"mood":"극지방 오로라 청록 보라 새벽하늘 빙하","layout":"immersive","font":"display","particle":"stars"},
    {"mood":"다크 아카데미아 빅토리안 고딕 도서관 촛불","layout":"editorial","font":"serif","particle":"none"},
    {"mood":"ABPS 스타일 순수 블랙 네온 그린 테크 UI","layout":"brutal","font":"sans","particle":"none"},
    {"mood":"인셉션 다크 에메랄드 그린 고급 교육 프리미엄","layout":"editorial","font":"serif","particle":"leaves"},
    {"mood":"겨울 새벽 눈 덮인 사찰 고요 집중 먹빛 설경","layout":"minimal","font":"serif","particle":"snow"},
    {"mood":"마젠타 핫핑크 플로럴 에디토리얼 여성적 우아함","layout":"magazine","font":"serif","particle":"petals"},
    {"mood":"미래 우주선 내부 홀로그램 코발트 블루 테크 UI","layout":"immersive","font":"mono","particle":"stars"},
    {"mood":"빈티지 옥스퍼드 도서관 가죽 책 양피지 세피아","layout":"editorial","font":"serif","particle":"none"},
    {"mood":"여름 밤 루프탑 인디고 블루 도시 스카이라인","layout":"immersive","font":"display","particle":"none"},
    {"mood":"19세기 파리 아방가르드 예술 포스터 타이포그래피","layout":"brutal","font":"display","particle":"none"},
    {"mood":"네온 팝아트 비비드 원색 90s 리트로 레이브","layout":"brutal","font":"display","particle":"none"},
    {"mood":"브루탈리즘 건축 콘크리트 모노크롬 강렬한 타이포","layout":"brutal","font":"sans","particle":"none"},
    {"mood":"가을 단풍 교정 은행나무 따뜻한 주황 갈색 노을","layout":"organic","font":"serif","particle":"leaves"},
    {"mood":"앰버 황금빛 위스키 바 재즈 다크 고급 무드","layout":"editorial","font":"serif","particle":"gold"},
    {"mood":"바이올렛 퍼플 팝 컬러 현대적 밝은 에너지","layout":"modern","font":"sans","particle":"none"},
    {"mood":"순수 흑백 영화 필름 노이즈 모노크롬 시네마","layout":"brutal","font":"mono","particle":"none"},
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
    # 야구/스포츠
    "야구장":"baseball+stadium+night+crowd",
    "야구":"baseball+stadium+crowd",
    "경기장":"sports+arena+stadium+night",
    "축구장":"football+pitch+soccer+field",
    "축구":"football+soccer+pitch+green",
    "농구장":"basketball+arena+court",
    "스포츠":"sports+stadium+dramatic",
    "관중":"stadium+crowd+lights",
    "골":"football+goal+stadium",
    "선수":"athlete+sports+action",
    # 도시/밤
    "사이버펑크":"cyberpunk+neon+city+rain+dark",
    "네온":"neon+lights+city+night",
    "도시":"city+skyline+night",
    "루프탑":"rooftop+city+night",
    "밤거리":"city+street+night+neon",
    # 자연
    "벚꽃":"cherry+blossom+spring+pink",
    "단풍":"autumn+leaves+fall+golden",
    "숲":"forest+trees+moody",
    "자작나무":"birch+forest+misty",
    "겨울":"winter+snow+cold+dramatic",
    "눈":"snow+winter+landscape",
    "오로라":"aurora+borealis+northern+lights",
    "바다":"ocean+sea+dramatic+waves",
    # 학습/공간
    "도서관":"library+books+dramatic+dark",
    "책":"books+library+study",
    "교실":"classroom+chalkboard+school",
    "칠판":"chalkboard+classroom",
    "사찰":"temple+zen+peaceful",
    # 우주/신비
    "우주":"space+cosmos+galaxy+nebula",
    "별":"stars+night+sky+milky+way",
    "플라네타리움":"planetarium+stars+dome",
    # 건축/디자인
    "건축":"brutalist+architecture+dramatic",
    "고딕":"gothic+dark+dramatic",
    "이집트":"egypt+pyramid+desert+golden",
    "사막":"desert+sand+golden+dunes",
    # 스타일
    "빈티지":"vintage+retro+film+grain",
    "흑백":"black+white+monochrome+dramatic",
    "앰버":"amber+golden+dark+warm",
    "골드":"gold+luxury+dark",
    "불꽃":"fire+flames+dark+dramatic",
    "안개":"foggy+mist+moody+atmospheric",
    # 영어도 지원
    "baseball":"baseball+stadium+night",
    "soccer":"soccer+stadium+crowd",
    "library":"library+books+dark",
    "space":"space+cosmos+stars",
    "fire":"fire+flames+dark",
    "neon":"neon+lights+city",
    "ocean":"ocean+waves+dramatic",
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
    s = re.sub(r"```json\s*", "", raw.strip())
    s = re.sub(r"```\s*", "", s).strip()
    fb, lb = s.find("{"), s.rfind("}")
    if fb > 0: s = s[fb:]
    if lb >= 0: s = s[:lb+1]
    def _try(x):
        try: return clean_obj(json.loads(x))
        except Exception: return None
    r = _try(s)
    if r: return r
    r = _try(s.replace("\n"," ").replace("\r",""))
    if r: return r
    depth, last = 0, -1
    for i, ch in enumerate(s):
        if ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0: last = i
    if last > 0:
        r = _try(s[:last+1])
        if r: return r
    raise ValueError(f"JSON 파싱 실패\n원본: {raw[:300]}")

def build_bg_url(mood: str) -> str:
    """무드 → 실사 배경 이미지 URL
    loremflickr.com 기반, + 키워드 구분자 사용
    """
    if not mood: return ""
    text = mood.lower()
    found = []
    # 긴 키워드 우선 매칭
    for ko, en in sorted(KO_BG.items(), key=lambda x: -len(x[0])):
        if ko.lower() in text:
            found = en.split("+")
            break
    # 영어 단어 직접 추출
    if not found:
        eng = [w for w in re.findall(r"[a-zA-Z]{4,}", mood)
               if w.lower() not in ("this","that","with","from","have","been")]
        found.extend(eng[:3])
    if not found:
        found = ["dramatic","dark","study"]
    tags = ",".join(list(dict.fromkeys(found))[:4])
    lock = random.randint(1, 99999)
    # 스포츠 계열은 로레플리커보다 unsplash가 더 정확
    sport_kw = ["football","soccer","baseball","basketball","stadium","pitch","court","arena","athlete"]
    if any(k in tags for k in sport_kw):
        # unsplash source (1920x900 landscape)
        return f"https://source.unsplash.com/1920x900/?{tags}&sig={lock}"
    return f"https://loremflickr.com/1920/900/{tags}?lock={lock}"

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
{color_hint}

디자인 규칙:
- 색상은 무드와 100% 일치해야 함 (야구장=짙은레드/블랙, 에시드=블랙/형광그린, 벚꽃=분홍/흰색 등)
- ⚠️ 대비(contrast) 필수: bg가 어두우면(#000~#333) textHex는 반드시 밝게(#E0 이상), bg가 밝으면(#EEE~#FFF) textHex는 어둡게(#111~#333). 배경과 텍스트 계열이 비슷하면 절대 안 됨
- ⚠️ c1(강조색)은 bg 위에서 확실히 눈에 띄는 색이어야 함 — bg와 같은 계열 금지
- extraCSS: 최소 150자, clip-path/box-shadow/text-shadow/transform/backdrop-filter 적극 사용
- heroStyle: "typographic"(배경색+거대타이포), "cinematic"(다크포토+영화), "billboard"(초대형텍스트), "editorial_bold"(에디토리얼), "split"(2컬럼), "immersive"(풀스크린포토) 중 무드에 맞는 것
- 어두운 테마는 c4와 bg가 완전 다른 색이어야 함 (c4=가장어두운 bg=약간밝은)
- extraCSS 내부 따옴표는 반드시 작은따옴표(') 사용

JSON만 반환 (한 줄):
{{"name":"2-4글자+이모지","dark":true,"heroStyle":"typographic","c1":"#hex","c2":"#hex","c3":"#hex","c4":"#hex","bg":"#hex","bg2":"#hex","bg3":"#hex","textHex":"#hex","textRgb":"r,g,b","bdAlpha":"rgba(r,g,b,.15)","displayFont":"Google Font name","bodyFont":"Noto Sans KR","fontWeights":"400;700;900","displayFontWeights":"400;700","borderRadiusPx":0,"btnBorderRadiusPx":2,"particle":"{seed.get('particle','none')}","ctaGradient":"linear-gradient(135deg,#hex,#hex)","extraCSS":"min 150 chars single-quote only"}}"""
    result = safe_json(call_ai(prompt, max_tokens=900))
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
        "신규 커리큘럼": '{"bannerSub":"10자이내","bannerTitle":"20자이내","brandTagline":"페이지 컨셉을 관통하는 브랜드 문구 1문장 (예: 우리의 강의실은, 영화관이 됩니다.)","bannerLead":"60-90자 수험생이 공감하는 구체적 고민을 찌르는 리드 문구","ctaCopy":"10자이내","ctaTitle":"CTA 제목","ctaSub":"30자이내","ctaBadge":"15자이내","statBadges":[],"introTitle":"20자이내","introDesc":"80-120자 강사만의 차별점과 학습 철학","introBio":"강사 학습법·특이점 포함 60자이내","introBadges":[],"whyTitle":"20자이내","whySub":"30자이내","whyReasons":[["이모지","12자제목","60자 학생 입장의 구체적 설명, 실제 변화 포함"],["이모지","12자","60자"],["이모지","12자","60자"]],"curriculumTitle":"20자이내","curriculumSub":"30자이내","curriculumSteps":[["01","8자제목","이 단계를 통해 무엇이 어떻게 달라지는지 학생 입장에서 50자 이상 설명","기간"],["02","8자","50자 이상","기간"],["03","8자","50자 이상","기간"],["04","8자","50자 이상","기간"]],"targetTitle":"20자이내","targetItems":["이런 학생을 대상으로 하는지 40-50자 구체적 상황 묘사","항목2 40자","항목3 40자","항목4 40자"],"reviews":[["지금도 쓸 것 같은 생생한 수강생 인용문 50-70자, 구체적 점수·방법 언급","이름","변화뱃지"],["50-70자 인용문","이름","뱃지"],["50-70자 인용문","이름","뱃지"]],"faqs":[["구체적 질문15자","명쾌한 답변 50자이상"],["질문","50자 답변"],["질문","50자 답변"]]}',
        "이벤트": '{"bannerSub":"10자","bannerTitle":"20자","brandTagline":"이벤트 분위기를 담은 브랜드 문구 1문장","bannerLead":"60-80자 긴박감 있는 리드","ctaCopy":"10자","ctaTitle":"CTA","ctaSub":"30자","ctaBadge":"15자","statBadges":[],"eventTitle":"20자","eventDesc":"50자이상","eventDetails":[["📅","이벤트 기간","날짜"],["🎯","대상","값"],["💰","혜택","값"]],"benefitsTitle":"20자","eventBenefits":[{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"01"},{"icon":"이모지","title":"혜택명","desc":"50자","badge":"8자","no":"02"},{"icon":"이모지","title":"혜택명","desc":"50자","badge":"8자","no":"03"}],"deadlineTitle":"20자","deadlineMsg":"70자 긴박감","reviews":[["50-70자 구체적 인용문","이름","뱃지"],["인용문","이름","뱃지"],["인용문","이름","뱃지"]]}',
        "기획전": '{"festHeroTitle":"20자","festHeroCopy":"30자","festHeroSub":"50자이상","brandTagline":"기획전 분위기를 담은 한 문장","festHeroStats":[["수치","라벨"],["수치","라벨"],["수치","라벨"],["수치","라벨"]],"festLineupTitle":"20자","festLineupSub":"40자","festLineup":[{"name":"강사명","tag":"분야8자","tagline":"강사를 한 문장으로 소개 40자","badge":"8자","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"소개 40자","badge":"뱃지","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"소개 40자","badge":"뱃지","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"소개 40자","badge":"뱃지","emoji":"이모지"}],"festBenefitsTitle":"20자","festBenefits":[{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"01"},{"icon":"이모지","title":"혜택명","desc":"50자","badge":"8자","no":"02"},{"icon":"이모지","title":"혜택명","desc":"50자","badge":"8자","no":"03"},{"icon":"이모지","title":"혜택명","desc":"50자","badge":"8자","no":"04"}],"festCtaTitle":"CTA제목","festCtaSub":"50자이상"}',
    }
    prompt = f"""대한민국 최고 수능 교육 랜딩페이지 카피라이터.

===강사 정보===
{inst_ctx}

===페이지 정보===
맥락: "{ctx}"
목적: {ptype} | 대상: {tgt} | 브랜드: {plabel}

===문구 품질 기준===
1. 강사 고유 커리큘럼명/학습법명 그대로 사용
2. 현대적 직접적 어조 — "체계적", "최고의" 같은 올드한 표현 금지
3. 수험생이 지금 느끼는 구체적 고민을 정확히 찌르는 문구
4. 실제처럼 들리는 수강평 (등급 변화, 학습법 언급 포함), 반드시 50자 이상
5. 수치(만족도%, 합격생수) 절대 금지 — statBadges:[], introBadges:[]
6. 한자 절대 금지
7. curriculumSteps 설명은 반드시 50자 이상 — 이 단계가 왜 필요한지, 어떻게 달라지는지 학생 입장에서 서술
8. targetItems는 반드시 40자 이상 — 학생의 구체적인 상황과 고민을 담을 것
9. brandTagline: 페이지의 컨셉/무드를 담은 독창적 한 문장 (예: 축구장 무드 → "우리의 훈련장은, 어디서도 멈추지 않는다.", 영화관 무드 → "우리의 강의실은, 영화관이 됩니다.", 우주 무드 → "지식의 끝, 우주만큼 멀리 가라.")

JSON만 반환:
{schemas.get(ptype, schemas['신규 커리큘럼'])}"""
    return safe_json(call_ai(prompt, max_tokens=3500))


def gen_section(sec_id: str) -> dict:
    inst_ctx = _get_instructor_context()
    schemas = {
        "banner": '{"bannerSub":"10자","bannerTitle":"20자","brandTagline":"컨셉을 담은 브랜드 한 문장","bannerLead":"60-90자 수험생이 공감하는 구체적 리드","ctaCopy":"10자","statBadges":[]}',
        "intro":  '{"introTitle":"20자","introDesc":"80-120자 강사 철학과 차별점","introBio":"강사 학습법 포함 60자","introBadges":[]}',
        "why":    '{"whyTitle":"20자","whySub":"30자","whyReasons":[["이모지","12자","학생 입장에서 구체적 설명 60자"],["이모지","12자","60자"],["이모지","12자","60자"]]}',
        "curriculum": '{"curriculumTitle":"20자","curriculumSub":"30자","curriculumSteps":[["01","8자","이 단계 통해 무엇이 달라지는지 50자 이상 설명","기간"],["02","8자","50자 이상","기간"],["03","8자","50자 이상","기간"],["04","8자","50자 이상","기간"]]}',
        "target": '{"targetTitle":"20자","targetItems":["이런 학생을 위한 40-50자 구체적 상황","항목2 40자","항목3 40자","항목4 40자"]}',
        "reviews": '{"reviews":[["지금도 쓸 것 같은 생생한 50-70자 인용문, 구체적 점수·방법 언급","이름","뱃지"],["50-70자 인용문","이름","뱃지"],["50-70자 인용문","이름","뱃지"]]}',
        "faq":    '{"faqs":[["15자 구체적 질문","명쾌한 답변 50자이상"],["질문","50자 이상 답변"],["질문","50자 이상 답변"]]}',
        "cta":    '{"ctaTitle":"CTA제목","ctaSub":"40자이상 수강신청 동기부여 문구","ctaCopy":"10자","ctaBadge":"15자"}',
    }
    sec_name = SEC_LABELS.get(sec_id, sec_id)
    schema = schemas.get(sec_id, '{"title":"제목","desc":"설명"}')
    prompt = f"""수능 교육 카피라이터. "{sec_name}" 섹션만 새롭게 생성.

{inst_ctx}
과목: {st.session_state.subject} | 브랜드: {st.session_state.purpose_label}

규칙: 강사 고유 학습법 직접 사용, 현대적 어조, 한자 금지, 수치 금지
JSON만: {schema}"""
    return safe_json(call_ai(prompt, max_tokens=900))


def gen_custom_sec(topic: str) -> dict:
    inst_ctx = _get_instructor_context()
    prompt = f"""수능 교육 랜딩페이지 "{topic}" 주제 섹션.
{inst_ctx} | 과목: {st.session_state.subject}
한자 금지. JSON만:
{{"tag":"8자이내","title":"20자이내","desc":"60자이내","items":[{{"icon":"이모지","title":"15자","desc":"45자"}},{{"icon":"이모지","title":"15자","desc":"45자"}},{{"icon":"이모지","title":"15자","desc":"45자"}}]}}"""
    return safe_json(call_ai(prompt, max_tokens=900))


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
    """AI 생성 테마의 배경-텍스트 대비 자동 보정"""
    bg_l  = _hex_luminance(ct.get("bg","#111"))
    tx_l  = _hex_luminance(ct.get("textHex","#fff"))
    ratio = (max(bg_l,tx_l)+0.05)/(min(bg_l,tx_l)+0.05)
    if ratio < 3.5:  # 대비 부족
        if bg_l < 0.18:  # 어두운 배경 → 텍스트를 밝게
            ct["textHex"] = "#F0F0F0"
            ct["textRgb"] = "240,240,240"
        else:  # 밝은 배경 → 텍스트를 어둡게
            ct["textHex"] = "#111111"
            ct["textRgb"] = "17,17,17"
    return ct


    if st.session_state.concept == "custom" and st.session_state.custom_theme:
        ct = st.session_state.custom_theme
        df  = ct.get("displayFont","Noto Sans KR")
        bf  = ct.get("bodyFont","Noto Sans KR")
        fw  = ct.get("fontWeights","400;700;900")
        dfw = ct.get("displayFontWeights","400;700")
        r   = ct.get("borderRadiusPx",4)
        rb  = ct.get("btnBorderRadiusPx",4)
        tr  = ct.get("textRgb","255,255,255")
        bd  = ct.get("bdAlpha","rgba(255,255,255,.12)")
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
a{text-decoration:none;color:inherit}

/* ── 인트로 애니메이션 ── */
.rv{opacity:0;transform:translateY(22px);transition:opacity .9s cubic-bezier(.16,1,.3,1),transform .9s cubic-bezier(.16,1,.3,1)}
.rv.on{opacity:1;transform:none}
.d1{transition-delay:.12s}.d2{transition-delay:.26s}.d3{transition-delay:.42s}.d4{transition-delay:.58s}
@keyframes fadeUp{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
@keyframes pulse-accent{0%,100%{opacity:.6}50%{opacity:1}}

/* ── 버튼 ── */
.btn-p{display:inline-flex;align-items:center;gap:8px;background:var(--c1);color:#fff;
  font-family:var(--fb);font-size:14px;font-weight:800;padding:14px 32px;
  border-radius:var(--r-btn,4px);border:none;cursor:pointer;
  box-shadow:0 4px 24px rgba(0,0,0,.25);
  transition:opacity .15s,transform .15s,box-shadow .15s;text-decoration:none;letter-spacing:.02em}
.btn-p:hover{opacity:.88;transform:translateY(-2px);box-shadow:0 8px 32px rgba(0,0,0,.35)}
.btn-s{display:inline-flex;align-items:center;gap:7px;background:transparent;
  color:var(--text);font-family:var(--fb);font-size:14px;font-weight:600;
  padding:13px 24px;border-radius:var(--r-btn,4px);border:1.5px solid var(--bd);
  cursor:pointer;transition:border-color .15s,color .15s;text-decoration:none}
.btn-s:hover{border-color:var(--c1);color:var(--c1)}

/* ── 섹션 기본 ── */
.sec{padding:clamp(60px,8vw,96px) clamp(28px,6vw,80px);position:relative}
.sec.alt{background:var(--bg2)}
.sec-inner{max-width:1200px;margin:0 auto}

/* ── 섹션 구분선 (대각선) ── */
.sec-diag-top::before{
  content:'';position:absolute;top:-1px;left:0;right:0;height:60px;
  background:var(--bg);
  clip-path:polygon(0 0,100% 0,100% 0,0 100%);z-index:1;
}
.sec-diag-bot::after{
  content:'';position:absolute;bottom:-1px;left:0;right:0;height:60px;
  background:var(--bg);
  clip-path:polygon(0 0,100% 100%,0 100%);z-index:1;
}

/* ── 태그라인 ── */
.tag-line{display:inline-flex;align-items:center;gap:9px;font-size:9.5px;font-weight:800;
  letter-spacing:.18em;text-transform:uppercase;color:var(--c1);margin-bottom:14px}
.tag-line::before{content:'';display:block;width:24px;height:2px;background:var(--c1)}

/* ── 섹션 타이틀 ── */
.sec-h2{font-family:var(--fh);font-size:clamp(26px,4vw,42px);font-weight:900;
  line-height:1.1;letter-spacing:-.04em;color:var(--text);margin-bottom:12px}
.sec-sub{font-size:14px;line-height:2;color:var(--t70);margin-bottom:40px;max-width:560px}

/* ── 카드 ── */
.card{background:var(--bg);border:1px solid var(--bd);border-radius:var(--r,4px);
  padding:24px;transition:transform .25s,box-shadow .25s}
.card:hover{transform:translateY(-4px);box-shadow:0 12px 40px rgba(0,0,0,.12)}

/* ── 강조 숫자 배경 데코 ── */
.num-deco{position:absolute;font-family:var(--fh);font-size:clamp(120px,18vw,220px);
  font-weight:900;line-height:1;opacity:.035;color:var(--c1);pointer-events:none;
  user-select:none;z-index:0}

/* ── 형광 강조 텍스트 ── */
.highlight{background:var(--c1);color:#fff;padding:0 6px;display:inline}

/* ── 타이포그래피 히어로 전용 ── */
.hero-word-accent{
  -webkit-text-stroke:2px var(--c1);
  color:transparent;
  font-family:var(--fh);
}
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
    kws   = SUBJ_KW.get(d["subject"], ["개념","기출","실전","파이널"])
    bg_url= cp.get("bg_photo_url", "")
    hs    = T.get("heroStyle", "typographic")
    s     = _bg_vars(bg_url, T["dark"])
    dark  = T["dark"]

    kh = "".join(f'<span style="font-size:9px;font-weight:800;padding:5px 14px;border-radius:var(--r-btn,4px);color:{s["c1c"]};border:1px solid {s["bdc"]};margin:2px;letter-spacing:.1em">{k}</span>' for k in kws)
    sh = "".join(f'<div><div style="font-family:var(--fh);font-size:clamp(20px,3vw,30px);font-weight:900;color:{s["c1c"]}">{sv}</div><div style="font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.5);margin-top:2px">{sl}</div></div>' for sv,sl in stats) if stats else ""
    inst = f'<div style="display:inline-flex;align-items:center;gap:8px;margin-top:20px;padding:6px 16px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:var(--r-btn,4px)"><span style="font-size:11px;color:rgba(255,255,255,.75);font-weight:600">{d["name"]} 선생님</span></div>' if d["name"] and bg_url else ""

    # ── 레이아웃 1: TYPOGRAPHIC (기본) ────────────
    if hs == "typographic":
        # 제목 첫 단어/글자를 거대 배경 데코로 사용
        deco_word = title[:3] if title else sub[:3]
        text_col = "#fff" if (dark or bg_url) else "var(--text)"
        t70_col  = "rgba(255,255,255,.7)" if (dark or bg_url) else "var(--t70)"
        accent_col = s["c1c"] if bg_url else "var(--c1)"
        return (
            f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:flex;flex-direction:column;justify-content:flex-end">'
            + s["overlay"]
            + f'<div style="position:absolute;top:0;left:0;right:0;bottom:0;background:linear-gradient(to top,rgba(0,0,0,.92) 0%,rgba(0,0,0,.25) 50%,transparent 100%);z-index:1;pointer-events:none"></div>'
            + f'<div style="position:absolute;top:-0.05em;right:-0.05em;font-family:var(--fh);font-size:38vw;font-weight:900;line-height:0.85;color:var(--c1);opacity:.04;pointer-events:none;overflow:hidden;z-index:1;user-select:none">{deco_word}</div>'
            + f'<div style="position:relative;z-index:2;padding:clamp(60px,8vw,100px) clamp(40px,7vw,100px);max-width:1000px">'
            + f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:28px"><div style="width:36px;height:3px;background:{accent_col}"></div><span style="font-size:9.5px;font-weight:800;letter-spacing:.22em;text-transform:uppercase;color:{accent_col}">{sub}</span></div>'
            + f'<h1 style="font-family:var(--fh);font-size:clamp(56px,9vw,130px);font-weight:900;line-height:.82;letter-spacing:-.05em;color:{text_col};margin-bottom:20px" class="st">{title}</h1>'
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
            # 시네마틱 레터박스 라인
            + f'<div style="position:absolute;top:0;left:0;right:0;height:6px;background:var(--c1);z-index:3"></div>'
            + f'<div style="position:absolute;bottom:0;left:0;right:0;height:6px;background:var(--c1);z-index:3"></div>'
            + f'<div style="position:relative;z-index:2;padding:80px clamp(40px,7vw,100px) 80px;display:grid;grid-template-columns:1fr 340px;gap:60px;align-items:flex-end">'
            + f'<div>'
            + f'<div style="display:inline-flex;align-items:center;gap:10px;margin-bottom:24px;padding:5px 18px;border:1.5px solid var(--c1);border-radius:var(--r-btn,2px)">'
            + f'<div style="width:8px;height:8px;background:var(--c1);border-radius:50%;animation:pulse-accent 1.5s ease-in-out infinite"></div>'
            + f'<span style="font-size:10px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:var(--c1)">{sub}</span></div>'
            + f'<h1 style="font-family:var(--fh);font-size:clamp(48px,7.5vw,110px);font-weight:900;line-height:.82;letter-spacing:-.04em;color:#fff;margin-bottom:16px" class="st">{title}</h1>'
            + (f'<div style="font-size:clamp(14px,1.6vw,19px);font-style:italic;font-weight:300;color:var(--c1);margin-bottom:18px;line-height:1.5;opacity:.9">{tagline}</div>' if tagline else "")
            + f'<p style="font-size:15px;line-height:2;color:rgba(255,255,255,.72);max-width:480px;border-left:3px solid var(--c1);padding-left:20px;margin-bottom:32px">{lead}</p>'
            + f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:28px">{kh}</div>'
            + f'<div style="display:flex;gap:12px">'
            + f'<a class="btn-p" href="#" style="font-size:15px;padding:16px 44px;letter-spacing:.04em">{cta} →</a>'
            + f'<a href="#" style="display:inline-flex;align-items:center;gap:8px;color:rgba(255,255,255,.7);font-weight:600;padding:15px 24px;border-radius:var(--r-btn,2px);border:1.5px solid rgba(255,255,255,.25);font-size:14px;text-decoration:none">미리보기</a>'
            + f'</div>'
            + (f'<div style="display:flex;gap:40px;margin-top:44px;padding-top:22px;border-top:1px solid rgba(255,255,255,.15)">{sh}</div>' if sh else "")
            + f'</div>'
            # 우측 미니 카드
            + f'<div style="padding:28px;background:rgba(0,0,0,.7);{s["blur"]};border:1px solid rgba(255,255,255,.12);border-radius:var(--r,4px)">'
            + f'<div style="font-family:var(--fh);font-size:11px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:var(--c1);margin-bottom:16px">강의 정보</div>'
            + "".join(f'<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid rgba(255,255,255,.1)"><span style="font-size:11px;color:rgba(255,255,255,.5)">{l}</span><span style="font-size:12px;font-weight:700;color:#fff">{v}</span></div>' for l,v in [["강의 대상",d["target"]],["과목",d["subject"]],["브랜드",d["purpose_label"][:14]]])
            + f'<a class="btn-p" href="#" style="width:100%;justify-content:center;margin-top:18px;display:flex;font-size:13px">{cta} →</a>'
            + f'</div></div></section>'
        )

    # ── 레이아웃 3: BILLBOARD (초대형 타이포만) ─────
    elif hs == "billboard":
        bg_col = "var(--bg)"
        line_col = "var(--c1)"
        title_parts = title.split()
        # 첫 줄은 채움, 두 번째 줄은 outline 처리
        line1 = title_parts[0] if title_parts else title
        line2 = " ".join(title_parts[1:]) if len(title_parts) > 1 else ""
        return (
            f'<section id="hero" style="min-height:100vh;background:{bg_col};position:relative;overflow:hidden;display:flex;flex-direction:column;justify-content:center;padding:80px clamp(40px,7vw,100px)">'
            + f'<div style="position:absolute;top:0;left:0;right:0;bottom:0;background:repeating-linear-gradient(0deg,transparent,transparent 79px,var(--bd) 79px,var(--bd) 80px);z-index:0;opacity:.3;pointer-events:none"></div>'
            + f'<div style="position:relative;z-index:1">'
            + f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:32px"><div style="width:48px;height:4px;background:var(--c1)"></div><span style="font-size:9.5px;font-weight:800;letter-spacing:.22em;text-transform:uppercase;color:var(--c1)">{sub}</span></div>'
            + f'<div style="font-family:var(--fh);font-size:clamp(72px,13vw,180px);font-weight:900;line-height:.82;letter-spacing:-.06em;color:var(--text);margin-bottom:4px" class="st">{line1}</div>'
            + (f'<div style="font-family:var(--fh);font-size:clamp(72px,13vw,180px);font-weight:900;line-height:.82;letter-spacing:-.06em;color:transparent;-webkit-text-stroke:2px var(--c1);">{line2}</div>' if line2 else "")
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
        text_col = "#fff" if (dark or bg_url) else "var(--text)"
        t70_col  = "rgba(255,255,255,.72)" if (dark or bg_url) else "var(--t70)"
        accent_c = s["c1c"] if bg_url else "var(--c1)"
        bd_c     = s["bdc"] if bg_url else "var(--bd)"
        return (
            f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:grid;grid-template-rows:auto 1fr auto">'
            + s["overlay"]
            + f'<div style="position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,.2) 0%,rgba(0,0,0,.75) 100%);z-index:1;pointer-events:none"></div>'
            # 헤더 바
            + f'<div style="position:relative;z-index:2;padding:28px clamp(40px,6vw,88px);display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid {bd_c}">'
            + f'<div style="font-family:var(--fh);font-size:15px;font-weight:900;color:{text_col};letter-spacing:.06em">{d["subject"].upper()} · {d["name"] if d["name"] else "강사"}</div>'
            + f'<div style="display:flex;gap:5px">{kh}</div>'
            + f'</div>'
            # 메인 콘텐츠
            + f'<div style="position:relative;z-index:2;padding:clamp(48px,6vw,80px) clamp(40px,6vw,88px);display:flex;flex-direction:column;justify-content:center">'
            + f'<div style="display:inline-flex;align-items:center;gap:8px;margin-bottom:20px"><span style="font-size:10px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:{accent_c}">{sub}</span></div>'
            + f'<h1 style="font-family:var(--fh);font-size:clamp(44px,7vw,96px);font-weight:900;line-height:.9;letter-spacing:-.04em;color:{text_col};max-width:800px;margin-bottom:16px" class="st">{title}</h1>'
            + (f'<div style="font-size:clamp(14px,1.5vw,18px);font-style:italic;font-weight:300;color:{accent_c};margin-bottom:20px;line-height:1.5;opacity:.9">{tagline}</div>' if tagline else "")
            + f'<div style="display:flex;gap:40px;align-items:flex-start;flex-wrap:wrap">'
            + f'<p style="font-size:clamp(13px,1.4vw,16px);line-height:1.95;color:{t70_col};max-width:420px;padding-left:20px;border-left:3px solid {accent_c}">{lead}</p>'
            + f'<div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0">'
            + f'<a class="btn-p" href="#" style="font-size:15px;padding:16px 44px">{cta} →</a>'
            + f'<a href="#" style="display:inline-flex;align-items:center;justify-content:center;gap:7px;color:{text_col};font-weight:600;padding:14px 24px;border-radius:var(--r-btn,4px);border:1.5px solid {bd_c};font-size:13px;text-decoration:none">강의 미리보기</a>'
            + f'</div></div></div>'
            # 하단 스탯
            + (f'<div style="position:relative;z-index:2;padding:24px clamp(40px,6vw,88px);border-top:1px solid {bd_c};display:flex;gap:48px">{sh}</div>' if sh else "<div></div>")
            + f'</section>'
        )

    # ── 레이아웃 5: SPLIT_BOLD ────────────────────
    elif hs == "split_bold":
        return (
            f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:grid;grid-template-columns:1fr 1fr">'
            + s["overlay"]
            # 좌측
            + f'<div style="position:relative;z-index:2;display:flex;flex-direction:column;justify-content:center;padding:clamp(60px,7vw,100px) clamp(32px,5vw,64px)">'
            + f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:24px"><div style="width:40px;height:3px;background:{s["c1c"] if bg_url else "var(--c1)"}"></div><span style="font-size:9.5px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:{s["c1c"] if bg_url else "var(--c1)"}">{sub}</span></div>'
            + f'<h1 style="font-family:var(--fh);font-size:clamp(38px,5.5vw,72px);font-weight:900;line-height:.88;letter-spacing:-.04em;{"color:#fff" if (dark or bg_url) else "color:var(--text)"};margin-bottom:20px" class="st">{title}</h1>'
            + f'<p style="font-size:14px;line-height:2;{"color:rgba(255,255,255,.72)" if (dark or bg_url) else "color:var(--t70)"};max-width:380px;margin-bottom:28px">{lead}</p>'
            + f'<div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:24px">{kh}</div>'
            + f'<a class="btn-p" href="#" style="align-self:flex-start;font-size:14px;padding:14px 36px">{cta} →</a>'
            + f'</div>'
            # 우측 — 강의 카드
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
            + f'<h1 style="font-family:var(--fh);font-size:clamp(48px,7.5vw,100px);font-weight:900;line-height:.84;letter-spacing:-.05em;color:#fff;margin-bottom:20px" class="st">{title}</h1>'
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
    mtags = "".join(f'<span style="background:var(--c1);color:#fff;font-size:10px;font-weight:800;padding:5px 16px;border-radius:var(--r-btn,4px);margin:3px 5px 3px 0;display:inline-flex;letter-spacing:.04em">{m}</span>' for m in methods[:4]) if methods else ""
    sq = f'<div style="margin-top:18px;padding:18px 22px;background:var(--bg3);border-radius:var(--r,4px);border-left:4px solid var(--c1)"><span style="font-size:14px;color:var(--text);font-style:italic;font-weight:500">"{slogan}"</span></div>' if slogan else ""
    # 좌우 분할 레이아웃
    return (
        f'<section class="sec alt" id="intro">'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:start;max-width:1200px;margin:0 auto">'
        f'<div class="rv">'
        f'<div class="tag-line">강사 소개</div>'
        f'<h2 class="sec-h2 st">{t}</h2>'
        f'<p class="sec-sub">{desc}</p>'
        f'{mtags and f"<div style=\'margin-bottom:16px\'>{mtags}</div>" or ""}'
        f'</div>'
        f'<div class="rv d1">'
        f'<div style="padding:24px 28px;border:1px solid var(--bd);border-radius:var(--r,4px);border-left:4px solid var(--c1)">'
        f'<p style="font-size:14px;line-height:2;color:var(--t70)">{bio}</p>'
        f'{sq}</div>'
        f'</div>'
        f'</div></section>'
    )


def sec_why(d, cp, T):
    t = strip_hanja(cp.get("whyTitle","이 강의가 필요한 이유"))
    s = strip_hanja(cp.get("whySub", f"{d['subject']} 1등급의 비결"))
    reasons = cp.get("whyReasons",[
        ["🎯","유형별 완전 정복","수능 출제 유형을 완전히 분석하여 어떤 문제도 흔들리지 않는 실력을 만듭니다."],
        ["📊","기출 데이터 분석","최근 5년 기출을 철저히 분석하여 실전에서 반드시 나오는 유형만 집중 훈련합니다."],
        ["⚡","실전 속도 훈련","정확도와 속도를 동시에 잡아 70분 안에 45문항을 완벽히 소화하는 훈련을 합니다."]
    ])
    safe_r = []
    for item in reasons:
        if isinstance(item, (list,tuple)) and len(item)>=3: safe_r.append((str(item[0]),str(item[1]),str(item[2])))
        elif isinstance(item, dict): safe_r.append((item.get("icon","✦"),item.get("title",""),item.get("desc","")))
    # 번호가 크게 보이는 카드
    rh = ""
    for i,(ic,tt,dc) in enumerate(safe_r, 1):
        rh += (
            f'<div class="card rv d{i}" style="position:relative;overflow:hidden;padding:28px 24px">'
            f'<div class="num-deco" style="font-size:120px;top:-20px;right:-10px;opacity:.05">{i:02d}</div>'
            f'<div style="position:relative;z-index:1">'
            f'<div style="width:52px;height:52px;border-radius:var(--r,4px);background:var(--c1);display:flex;align-items:center;justify-content:center;font-size:22px;margin-bottom:16px">{ic}</div>'
            f'<div style="font-family:var(--fh);font-size:16px;font-weight:700;margin-bottom:10px;letter-spacing:-.02em" class="st">{strip_hanja(tt)}</div>'
            f'<p style="font-size:13px;line-height:1.9;color:var(--t70)">{strip_hanja(dc)}</p>'
            f'</div></div>'
        )
    return (
        f'<section class="sec" id="why">'
        f'<div style="max-width:1200px;margin:0 auto">'
        f'<div class="rv"><div class="tag-line">수강 이유</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{s}</p></div>'
        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px">{rh}</div>'
        f'</div></section>'
    )


def sec_curriculum(d, cp, T):
    t = strip_hanja(cp.get("curriculumTitle",f"{d['purpose_label']} 커리큘럼"))
    s = strip_hanja(cp.get("curriculumSub","4단계 완성 로드맵"))
    steps = cp.get("curriculumSteps",[
        ["01","개념 완성","핵심 개념과 공식, 왜 이 단계가 필요한지 이해합니다.","4주"],
        ["02","유형 훈련","기출 완전 분석으로 실전 패턴을 파악합니다.","4주"],
        ["03","심화 특훈","고난도 아이디어를 완전히 내 것으로 만듭니다.","3주"],
        ["04","파이널","실수 제거와 시간 배분으로 실전을 완성합니다.","3주"],
    ])
    # 좌측 상세 설명 + 우측 스텝 카드 레이아웃
    sh = ""
    for idx, step in enumerate(steps):
        no,tt,dc,du = str(step[0]),str(step[1]),str(step[2]),str(step[3]) if len(step)>3 else "4주"
        is_last = idx == len(steps)-1
        sh += (
            f'<div class="rv d{min(idx+1,4)}" style="display:flex;gap:20px;align-items:flex-start;padding-bottom:{"0" if is_last else "28px"};{"" if is_last else "border-bottom:1px solid var(--bd)"};margin-bottom:{"0" if is_last else "28px"}">'
            f'<div style="flex-shrink:0;width:56px;height:56px;border-radius:var(--r,4px);background:var(--c1);display:flex;align-items:center;justify-content:center;font-family:var(--fh);font-size:14px;font-weight:900;color:#fff;letter-spacing:.05em">0{idx+1}</div>'
            f'<div style="flex:1">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
            f'<div style="font-family:var(--fh);font-size:16px;font-weight:700;letter-spacing:-.02em" class="st">{strip_hanja(tt)}</div>'
            f'<span style="font-size:9px;background:var(--bg3);color:var(--c1);padding:3px 10px;border-radius:100px;font-weight:700;border:1px solid var(--bd)">{du}</span>'
            f'</div>'
            f'<p style="font-size:13px;line-height:1.8;color:var(--t70)">{strip_hanja(dc)}</p>'
            f'</div></div>'
        )
    return (
        f'<section class="sec alt" id="curriculum">'
        f'<div style="display:grid;grid-template-columns:1fr 1.4fr;gap:72px;align-items:start;max-width:1200px;margin:0 auto">'
        f'<div class="rv" style="position:sticky;top:60px">'
        f'<div class="tag-line">커리큘럼</div>'
        f'<h2 class="sec-h2 st">{t}</h2>'
        f'<p class="sec-sub">{s}</p>'
        f'<div style="padding:20px 24px;background:var(--c1);border-radius:var(--r,4px);margin-top:8px">'
        f'<div style="font-size:10px;font-weight:800;letter-spacing:.15em;text-transform:uppercase;color:rgba(255,255,255,.6);margin-bottom:8px">TOTAL</div>'
        f'<div style="font-family:var(--fh);font-size:36px;font-weight:900;color:#fff">{len(steps)*4}주</div>'
        f'<div style="font-size:11px;color:rgba(255,255,255,.7);margin-top:4px">{len(steps)}단계 완성 과정</div>'
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
        f"{d['subject']} 상위권 도약을 원하는 분"])]
    ih = "".join(
        f'<div class="rv d{min(i+1,4)}" style="display:flex;align-items:center;gap:16px;padding:18px 22px;border:1px solid var(--bd);border-radius:var(--r,4px);background:var(--bg);transition:border-color .2s" onmouseover="this.style.borderColor=\'var(--c1)\'" onmouseout="this.style.borderColor=\'var(--bd)\'">'
        f'<div style="width:32px;height:32px;min-width:32px;border-radius:var(--r-btn,4px);background:var(--c1);display:flex;align-items:center;justify-content:center;font-family:var(--fh);font-size:13px;font-weight:900;color:#fff">{i+1:02d}</div>'
        f'<span style="font-size:14px;font-weight:600;line-height:1.5;color:var(--text)">{txt}</span>'
        f'<div style="margin-left:auto;font-size:16px;color:var(--c1)">→</div>'
        f'</div>'
        for i,txt in enumerate(items)
    )
    return (
        f'<section class="sec" id="target">'
        f'<div style="max-width:800px;margin:0 auto">'
        f'<div class="rv" style="text-align:center;margin-bottom:40px"><div class="tag-line" style="justify-content:center">수강 대상</div><h2 class="sec-h2 st" style="text-align:center">{t}</h2></div>'
        f'<div style="display:flex;flex-direction:column;gap:10px">{ih}</div>'
        f'</div></section>'
    )


def sec_reviews(d, cp, T):
    reviews = cp.get("reviews",[
        [f'"개념이 이렇게 명확하게 보인 적이 없었어요. {d["subject"]} 공부가 달라졌습니다."',"고3 김OO","등급 향상"],
        ['"3주 만에 독해 속도가 확실히 빨라졌어요. 실전에서 시간이 남는 게 느껴졌습니다."',"N수 이OO","실전 완성"],
        [f'"선생님 덕분에 {d["subject"]} 구조가 보이기 시작했어요. 빈칸이 겁나지 않습니다."',"고2 박OO","자신감 회복"],
    ])
    rh = ""
    for i,(txt,nm,badge) in enumerate(reviews):
        rh += (
            f'<div class="card rv d{min(i+1,3)}" style="display:flex;flex-direction:column;gap:12px;padding:28px">'
            f'<div style="display:flex;gap:2px;color:#F59E0B;font-size:12px">{"★"*5}</div>'
            f'<p style="font-size:13.5px;line-height:1.9;font-weight:500;flex:1">{strip_hanja(txt)}</p>'
            f'<div style="display:flex;align-items:center;justify-content:space-between;padding-top:12px;border-top:1px solid var(--bd)">'
            f'<span style="font-size:11px;color:var(--t45)">— {nm} 학생</span>'
            f'<span style="font-size:9.5px;background:var(--bg3);color:var(--c1);padding:3px 12px;border-radius:var(--r-btn,100px);font-weight:700;border:1px solid var(--bd)">{badge}</span>'
            f'</div></div>'
        )
    return (
        f'<section class="sec alt" id="reviews">'
        f'<div style="max-width:1200px;margin:0 auto">'
        f'<div class="rv" style="margin-bottom:40px"><div class="tag-line">수강평</div><h2 class="sec-h2 st">생생한 수강생 후기</h2></div>'
        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px">{rh}</div>'
        f'</div></section>'
    )


def sec_faq(d, cp, T):
    raw = cp.get("faqs",[
        ["수강 기간은 얼마나 되나요?","기본 30일이며, 연장권으로 최대 90일 가능합니다."],
        ["교재는 별도 구매인가요?","별도 구매이며, 신청 페이지에서 함께 구매하실 수 있습니다."],
        ["모바일에서도 수강 가능한가요?","PC와 모바일 모두 가능합니다."],
    ])
    faqs = []
    for item in raw:
        if isinstance(item, dict): faqs.append([item.get("question",item.get("q","")), item.get("answer",item.get("a",""))])
        elif isinstance(item, list) and len(item)>=2: faqs.append([str(item[0]),str(item[1])])
    fh = ""
    for i,(q,a) in enumerate(faqs):
        fh += (
            f'<div class="rv d{min(i+1,3)}" style="margin-bottom:8px">'
            f'<div style="border:1px solid var(--bd);border-radius:var(--r,4px);overflow:hidden">'
            f'<div style="padding:15px 20px;background:var(--bg3);display:flex;gap:12px;align-items:flex-start">'
            f'<span style="color:var(--c1);font-weight:900;font-size:15px;flex-shrink:0;font-family:var(--fh)">Q.</span>'
            f'<span style="font-weight:700;font-size:13.5px;line-height:1.6">{strip_hanja(q)}</span></div>'
            f'<div style="padding:14px 20px;background:var(--bg);display:flex;gap:12px;align-items:flex-start">'
            f'<span style="color:var(--t45);font-weight:700;font-size:15px;flex-shrink:0;font-family:var(--fh)">A.</span>'
            f'<span style="font-size:13px;line-height:1.85;color:var(--t70)">{strip_hanja(a)}</span></div>'
            f'</div></div>'
        )
    return (
        f'<section class="sec" id="faq">'
        f'<div style="max-width:800px;margin:0 auto">'
        f'<div class="rv" style="margin-bottom:36px"><div class="tag-line">FAQ</div><h2 class="sec-h2 st">자주 묻는 질문</h2></div>'
        f'{fh}</div></section>'
    )


def sec_cta(d, cp, T):
    tt    = strip_hanja(cp.get("ctaTitle", f"지금 바로 시작해<br>{d['subject']} 1등급을 확보하세요"))
    sub   = strip_hanja(cp.get("ctaSub",   f"{d['name']} 선생님과 함께라면 가능합니다." if d["name"] else f"{d['subject']} 1등급, 지금 시작하세요."))
    cc    = strip_hanja(cp.get("ctaCopy",  "지금 수강신청하기"))
    badge = strip_hanja(cp.get("ctaBadge", f"{d['target']} 전용"))
    return (
        f'<section style="padding:clamp(72px,10vw,112px) clamp(28px,6vw,72px);text-align:center;position:relative;overflow:hidden;background:{T["cta"]}">'
        f'<div style="position:absolute;top:-150px;right:-150px;width:500px;height:500px;border-radius:50%;background:rgba(255,255,255,.03);pointer-events:none"></div>'
        f'<div style="position:absolute;bottom:-100px;left:-100px;width:400px;height:400px;border-radius:50%;background:rgba(255,255,255,.04);pointer-events:none"></div>'
        f'<div style="position:relative;z-index:1">'
        f'<div style="display:inline-block;background:rgba(255,255,255,.12);padding:6px 20px;border-radius:100px;font-size:10px;font-weight:800;color:#fff;margin-bottom:22px;letter-spacing:.14em;text-transform:uppercase">{badge}</div>'
        f'<h2 style="font-family:var(--fh);font-size:clamp(28px,5vw,56px);font-weight:900;line-height:1.08;letter-spacing:-.04em;color:#fff;margin-bottom:14px">{tt}</h2>'
        f'<p style="color:rgba(255,255,255,.6);font-size:15px;margin-bottom:42px;max-width:440px;margin-left:auto;margin-right:auto">{sub}</p>'
        f'<div style="display:flex;gap:14px;justify-content:center;flex-wrap:wrap">'
        f'<a style="display:inline-flex;align-items:center;gap:8px;background:#fff;color:#0A0A0A;font-weight:800;padding:17px 52px;border-radius:var(--r-btn,4px);font-size:16px;text-decoration:none;letter-spacing:.02em" href="#">{cc} →</a>'
        f'<a style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.1);backdrop-filter:blur(8px);color:rgba(255,255,255,.82);font-weight:600;padding:16px 32px;border-radius:var(--r-btn,4px);border:1.5px solid rgba(255,255,255,.3);font-size:14px;text-decoration:none" href="#">카카오톡 문의</a>'
        f'</div></div></section>'
    )


def sec_event_overview(d, cp, T):
    t = strip_hanja(cp.get("eventTitle", d["purpose_label"]))
    desc = strip_hanja(cp.get("eventDesc","이 이벤트는 기간 한정으로 진행됩니다."))
    details = cp.get("eventDetails",[["📅","이벤트 기간","2026. 4. 1 — 4. 30"],["🎯","대상","고3·N수"],["💰","혜택","최대 30% 할인"]])
    dh = "".join(f'<div class="card rv d{i+1}" style="text-align:center;padding:32px 20px"><div style="font-size:36px;margin-bottom:14px">{ic}</div><div style="font-size:10px;font-weight:800;color:var(--c1);letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px">{lb}</div><div style="font-family:var(--fh);font-size:19px;font-weight:700">{vl}</div></div>' for i,(ic,lb,vl) in enumerate(details))
    return (f'<section class="sec" id="event-overview"><div style="max-width:1200px;margin:0 auto"><div class="rv"><div class="tag-line">이벤트 개요</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{desc}</p></div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px">{dh}</div></div></section>')


def sec_event_benefits(d, cp, T):
    t = strip_hanja(cp.get("benefitsTitle","이벤트 특별 혜택"))
    benefits = cp.get("eventBenefits",[{"icon":"🎁","title":"수강료 특가","desc":"이벤트 기간 최대 30% 할인.","badge":"최대 30%","no":"01"},{"icon":"📚","title":"교재 무료 제공","desc":"핵심 교재 무료 제공.","badge":"무료","no":"02"},{"icon":"🔥","title":"라이브 특강","desc":"매주 토요일 라이브 특강.","badge":"매주","no":"03"}])
    bh = "".join(f'<div class="card rv d{i+1}" style="display:grid;grid-template-columns:64px 1fr;gap:20px;align-items:flex-start;padding:24px"><div style="width:64px;height:64px;border-radius:var(--r,4px);background:linear-gradient(135deg,var(--c1),var(--c2));display:flex;align-items:center;justify-content:center;font-size:28px;flex-shrink:0">{b["icon"]}</div><div><div style="display:flex;align-items:center;gap:8px;margin-bottom:8px"><span style="font-size:9px;font-weight:800;color:var(--c1);opacity:.7">NO.{b["no"]}</span><span style="background:var(--c1);color:#fff;font-size:9px;font-weight:800;padding:2px 10px;border-radius:100px">{b["badge"]}</span></div><div style="font-family:var(--fh);font-size:15px;font-weight:700;margin-bottom:7px" class="st">{strip_hanja(b["title"])}</div><p style="font-size:12.5px;line-height:1.85;color:var(--t70)">{strip_hanja(b["desc"])}</p></div></div>' for i,b in enumerate(benefits))
    return f'<section class="sec alt" id="event-benefits"><div style="max-width:1200px;margin:0 auto"><div class="rv"><div class="tag-line">이벤트 혜택</div><h2 class="sec-h2 st">{t}</h2></div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px">{bh}</div></div></section>'


def sec_event_deadline(d, cp, T):
    t = strip_hanja(cp.get("deadlineTitle","마감 안내"))
    msg = strip_hanja(cp.get("deadlineMsg","이벤트는 기간 한정으로 운영됩니다."))
    cc = strip_hanja(cp.get("ctaCopy","이벤트 신청하기"))
    return (f'<section class="sec" id="event-deadline" style="background:{T["cta"]};text-align:center"><div class="rv"><div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.15);padding:6px 20px;border-radius:100px;font-size:11px;font-weight:800;color:#fff;margin-bottom:24px">⏰ 마감 안내</div><h2 style="font-family:var(--fh);font-size:clamp(26px,4vw,44px);font-weight:900;color:#fff;margin-bottom:18px" class="st">{t}</h2><p style="color:rgba(255,255,255,.7);font-size:15px;line-height:1.9;margin-bottom:40px;max-width:460px;margin-left:auto;margin-right:auto">{msg}</p><a style="display:inline-flex;align-items:center;gap:8px;background:#fff;color:#0A0A0A;font-weight:800;padding:16px 52px;border-radius:var(--r-btn,4px);font-size:16px;text-decoration:none" href="#">{cc} →</a></div></section>')


def sec_fest_hero(d, cp, T):
    t = strip_hanja(cp.get("festHeroTitle",f"{d['subject']} 기획전"))
    cc = strip_hanja(cp.get("festHeroCopy","최고의 강사들이 한 자리에"))
    sub = strip_hanja(cp.get("festHeroSub",f"수능 {d['subject']} 전 강사 라인업."))
    stats = cp.get("festHeroStats",[])
    sh = "".join(f'<div style="text-align:center"><div style="font-family:var(--fh);font-size:clamp(22px,3.5vw,36px);font-weight:900;color:var(--c1)">{sv}</div><div style="font-size:9px;color:rgba(255,255,255,.5);font-weight:700;letter-spacing:.12em;text-transform:uppercase;margin-top:4px">{sl}</div></div>' for sv,sl in stats) if stats else ""
    return (f'<section id="fest-hero" style="position:relative;min-height:80vh;overflow:hidden;background:{T["cta"]};display:flex;flex-direction:column;justify-content:center;text-align:center;padding:clamp(80px,10vw,120px) clamp(28px,6vw,80px)"><div style="position:absolute;inset:0;background:radial-gradient(ellipse 80% 70% at 50% 30%,rgba(255,255,255,.07),transparent 65%);pointer-events:none"></div><div style="position:relative;z-index:2"><div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.12);backdrop-filter:blur(8px);padding:7px 22px;border-radius:var(--r-btn,4px);font-size:11px;font-weight:800;color:#fff;margin-bottom:28px;border:1px solid rgba(255,255,255,.2)">🏆 {d["subject"]} 기획전</div><h1 style="font-family:var(--fh);font-size:clamp(44px,8vw,112px);font-weight:900;line-height:.82;letter-spacing:-.05em;color:#fff;margin-bottom:22px" class="st">{t}</h1><p style="font-size:clamp(18px,2.5vw,24px);color:rgba(255,255,255,.78);margin-bottom:12px;font-weight:700">{cc}</p><p style="font-size:15px;color:rgba(255,255,255,.52);margin-bottom:52px;max-width:500px;margin-left:auto;margin-right:auto">{sub}</p>'+(f'<div style="display:flex;gap:52px;justify-content:center;flex-wrap:wrap;padding-top:40px;border-top:1px solid rgba(255,255,255,.15)">{sh}</div>' if sh else "")+'</div></section>')


def sec_fest_lineup(d, cp, T):
    t = strip_hanja(cp.get("festLineupTitle","강사 라인업"))
    s = strip_hanja(cp.get("festLineupSub",f"{d['subject']} 전 영역 최강 강사진"))
    lineup = cp.get("festLineup",[{"name":"강사A","tag":"독해·문법","tagline":"수능 영어 독해의 정석","badge":"베스트셀러","emoji":"📖"},{"name":"강사B","tag":"EBS 연계","tagline":"EBS 연계율 완벽 적중","badge":"적중률 1위","emoji":"🎯"},{"name":"강사C","tag":"어법·어휘","tagline":"어법·어휘 전문 빠른 풀이","badge":"속도UP","emoji":"⚡"},{"name":"강사D","tag":"파이널","tagline":"수능 D-30 파이널 완성","badge":"파이널 특화","emoji":"🏆"}])
    lh = "".join(f'<div class="card rv d{min(i+1,4)}" style="text-align:center;padding:32px 24px"><div style="font-size:44px;margin-bottom:16px">{l["emoji"]}</div><div style="display:inline-flex;align-items:center;gap:6px;background:var(--bg3);color:var(--c1);font-size:9.5px;font-weight:800;padding:4px 14px;border-radius:var(--r-btn,100px);margin-bottom:14px;border:1px solid var(--bd)">{strip_hanja(l["tag"])}</div><div style="font-family:var(--fh);font-size:20px;font-weight:900;margin-bottom:9px" class="st">{strip_hanja(l["name"])}</div><p style="font-size:12.5px;line-height:1.75;color:var(--t70);margin-bottom:14px">{strip_hanja(l["tagline"])}</p><span style="font-size:10px;background:var(--c1);color:#fff;padding:4px 16px;border-radius:100px;font-weight:800">{strip_hanja(l["badge"])}</span></div>' for i,l in enumerate(lineup))
    return f'<section class="sec alt" id="fest-lineup"><div style="max-width:1200px;margin:0 auto"><div class="rv"><div class="tag-line">강사 라인업</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{s}</p></div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px">{lh}</div></div></section>'


def sec_fest_benefits(d, cp, T):
    t = strip_hanja(cp.get("festBenefitsTitle","기획전 특별 혜택"))
    benefits = cp.get("festBenefits",[{"icon":"🎁","title":"전 강사 통합 수강료 특가","desc":"최대 30% 추가 할인.","badge":"최대 30%","no":"01"},{"icon":"📚","title":"통합 학습 자료 무료","desc":"통합 교재 및 기출 자료 무료.","badge":"무료 제공","no":"02"},{"icon":"🔥","title":"주간 라이브 특강","desc":"매주 전 강사 참여 라이브.","badge":"전 강사","no":"03"},{"icon":"🏆","title":"목표 등급 보장","desc":"목표 등급 미달성 시 재수강.","badge":"성적 보장","no":"04"}])
    bh = "".join(f'<div class="card rv d{min(i+1,4)}" style="display:grid;grid-template-columns:64px 1fr;gap:20px;align-items:flex-start;padding:24px"><div style="width:64px;height:64px;border-radius:var(--r,4px);background:linear-gradient(135deg,var(--c1),var(--c2));display:flex;align-items:center;justify-content:center;font-size:28px;flex-shrink:0">{b["icon"]}</div><div><div style="display:flex;align-items:center;gap:8px;margin-bottom:8px"><span style="font-size:9px;font-weight:800;color:var(--c1);opacity:.7">NO.{b["no"]}</span><span style="background:var(--c1);color:#fff;font-size:9px;font-weight:800;padding:2px 10px;border-radius:100px">{b["badge"]}</span></div><div style="font-family:var(--fh);font-size:15px;font-weight:700;margin-bottom:7px" class="st">{strip_hanja(b["title"])}</div><p style="font-size:12.5px;line-height:1.85;color:var(--t70)">{strip_hanja(b["desc"])}</p></div></div>' for i,b in enumerate(benefits))
    return f'<section class="sec" id="fest-benefits"><div style="max-width:1200px;margin:0 auto"><div class="rv"><div class="tag-line">기획전 혜택</div><h2 class="sec-h2 st">{t}</h2></div><div style="display:grid;grid-template-columns:repeat(2,1fr);gap:16px">{bh}</div></div></section>'


def sec_fest_cta(d, cp, T):
    t = strip_hanja(cp.get("festCtaTitle",f"지금 바로 {d['subject']} 기획전<br>전체 강사 라인업을 만나세요"))
    s = strip_hanja(cp.get("festCtaSub",f"최고의 강사들과 함께 {d['subject']} 1등급 완성."))
    return (f'<section style="padding:clamp(72px,10vw,112px) clamp(28px,6vw,72px);text-align:center;position:relative;overflow:hidden;background:{T["cta"]}"><div style="position:absolute;top:-120px;left:50%;transform:translateX(-50%);width:700px;height:700px;border-radius:50%;background:rgba(255,255,255,.03);pointer-events:none"></div><div style="position:relative;z-index:1"><div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.12);backdrop-filter:blur(8px);padding:7px 22px;border-radius:var(--r-btn,4px);font-size:11px;font-weight:800;color:#fff;margin-bottom:26px;border:1px solid rgba(255,255,255,.2)">🏆 {d["subject"]} 기획전 통합 신청</div><h2 style="font-family:var(--fh);font-size:clamp(28px,5vw,60px);font-weight:900;line-height:1.05;letter-spacing:-.04em;color:#fff;margin-bottom:18px">{t}</h2><p style="color:rgba(255,255,255,.6);font-size:15px;line-height:1.85;margin-bottom:44px;max-width:480px;margin-left:auto;margin-right:auto">{s}</p><div style="display:flex;gap:14px;justify-content:center;flex-wrap:wrap"><a style="display:inline-flex;align-items:center;gap:8px;background:#fff;color:#0A0A0A;font-weight:800;padding:18px 52px;border-radius:var(--r-btn,4px);font-size:16px;text-decoration:none" href="#">기획전 통합 신청 →</a><a style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.1);backdrop-filter:blur(8px);color:rgba(255,255,255,.82);font-weight:600;padding:17px 32px;border-radius:var(--r-btn,4px);border:1.5px solid rgba(255,255,255,.3);font-size:14px;text-decoration:none" href="#">강사 개별 신청</a></div></div></section>')


def sec_custom(d, cp, T):
    c = cp.get("custom_section_data", {})
    if not c: return ""
    tag   = strip_hanja(c.get("tag","추가 안내"))
    title = strip_hanja(c.get("title","추가 섹션"))
    items = c.get("items",[])
    desc  = strip_hanja(c.get("desc",""))
    if items:
        ih = "".join(f'<div class="card rv d{min(i+1,3)}"><div style="display:flex;align-items:center;gap:12px;margin-bottom:12px"><div style="width:40px;height:40px;min-width:40px;border-radius:var(--r,4px);background:var(--c1);display:flex;align-items:center;justify-content:center;font-size:18px">{it.get("icon","✦")}</div><div style="font-family:var(--fh);font-size:14px;font-weight:700" class="st">{strip_hanja(it.get("title",""))}</div></div><p style="font-size:12.5px;line-height:1.9;color:var(--t70)">{strip_hanja(it.get("desc",""))}</p></div>' for i,it in enumerate(items))
        cols = f"repeat({min(len(items),3)},1fr)"
        body = f'<div style="display:grid;grid-template-columns:{cols};gap:14px" class="rv d1">{ih}</div>'
    else:
        body = f'<div class="rv d1"><p style="font-size:14px;line-height:1.9;color:var(--t70)">{desc}</p></div>'
    return f'<section class="sec" id="custom-section"><div style="max-width:1200px;margin:0 auto"><div class="rv"><div class="tag-line">{tag}</div><h2 class="sec-h2 st">{title}</h2></div>{body}</div></section>'


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
        "event_overview":sec_event_overview,"event_benefits":sec_event_benefits,
        "event_deadline":sec_event_deadline,"fest_hero":sec_fest_hero,
        "fest_lineup":sec_fest_lineup,"fest_benefits":sec_fest_benefits,
        "fest_cta":sec_fest_cta,"custom_section":sec_custom,
    }
    body = "\n".join(mp[s](d,cp,T) for s in secs if s in mp)
    ttl  = cp.get("bannerTitle", cp.get("festHeroTitle", d["purpose_label"]))
    particle_js = _particle_js(T.get("particle","none"))
    return (
        f'<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"/>'
        f'<meta name="viewport" content="width=device-width,initial-scale=1.0"/>'
        f'<title>{d["name"]} {d["subject"]} · {ttl}</title>'
        f'<link rel="preconnect" href="https://fonts.googleapis.com"/>'
        f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>'
        f'<link href="{T["fonts"]}" rel="stylesheet"/>'
        f'<style>:root{{{T["vars"]}}}{BASE_CSS}{T["extra_css"]}{dc}</style>'
        f'</head><body>{body}{particle_js}'
        f'<script>const ro=new IntersectionObserver(es=>{{es.forEach(e=>{{if(e.isIntersecting){{e.target.classList.add("on");ro.unobserve(e.target);}}}});}},{{threshold:.08}});document.querySelectorAll(".rv").forEach(el=>ro.observe(el));</script>'
        f'</body></html>'
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
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🎓 강사 페이지 빌더 Pro")
    st.caption("수능 강사 랜딩페이지 AI 생성기 v7")
    st.divider()

    # API Key
    st.markdown('<div class="sec-hdr">🔑 GROQ API KEY</div>', unsafe_allow_html=True)
    api_in = st.text_input("API Key", type="password", value=st.session_state.api_key,
                           placeholder="gsk_...", label_visibility="collapsed")
    if api_in != st.session_state.api_key:
        st.session_state.api_key = api_in
    if st.session_state.api_key:
        st.success("✓ Groq API 키 입력됨 (완전 무료)", icon="✅")
    else:
        st.markdown('<a href="https://console.groq.com" target="_blank" style="font-size:11px;color:#5A6A8A">👆 console.groq.com → API Keys → Create</a>', unsafe_allow_html=True)

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
    if uploaded_img is not None:
        b64 = base64.b64encode(uploaded_img.read()).decode()
        mime = uploaded_img.type or "image/jpeg"
        st.session_state.uploaded_bg_b64 = f"data:{mime};base64,{b64}"
        st.session_state.bg_photo_url = ""
        st.success(f"✓ '{uploaded_img.name}' 업로드됨!")
        st.rerun()
    if st.session_state.uploaded_bg_b64:
        if st.button("🗑 업로드 이미지 제거", use_container_width=True, key="rm_bg"):
            st.session_state.uploaded_bg_b64 = ""
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
    st.markdown('<div class="sec-hdr">👤 강사 정보</div>', unsafe_allow_html=True)
    na_, su_ = st.columns([3, 2])
    with na_:
        nm = st.text_input("강사명", value=st.session_state.instructor_name,
                           placeholder="강사명", label_visibility="collapsed")
        st.session_state.instructor_name = nm
    with su_:
        sb = st.selectbox("과목", ["영어","수학","국어","사회","과학"],
                          index=["영어","수학","국어","사회","과학"].index(st.session_state.subject),
                          label_visibility="collapsed")
        st.session_state.subject = sb

    if st.button("🔍 강사 정보 자동 검색", use_container_width=True):
        if not nm: st.warning("강사명을 입력해주세요")
        elif not st.session_state.api_key: st.warning("API 키를 입력해주세요")
        else:
            with st.spinner(f"{nm} 선생님 정보 검색 중..."):
                try:
                    p = search_instructor(nm, sb)
                    st.session_state.inst_profile = p
                    if p.get("found"):
                        st.success(f"✓ {nm} 선생님 정보 검색 완료!")
                        if p.get("slogan"): st.caption(f'💬 "{p["slogan"]}"')
                        methods = [m for m in (p.get("signatureMethods") or []) if m and m != "없음"]
                        if methods: st.caption(f'📚 {", ".join(methods)}')
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
        chk = st.checkbox(SEC_LABELS.get(sid,sid),
                          value=sid in st.session_state.active_sections, key=f"sec_{sid}")
        if chk and sid not in st.session_state.active_sections:
            st.session_state.active_sections.append(sid)
        elif not chk and sid in st.session_state.active_sections:
            st.session_state.active_sections.remove(sid)

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

L, R = st.columns([1, 2], gap="large")

with L:
    st.markdown("### ✍️ AI 문구 생성")
    st.caption(PURPOSE_HINTS[st.session_state.purpose_type])
    ph_map = {
        "신규 커리큘럼": "예: 2026 수능 영어 파이널. 션티 선생님의 KISS Logic 방법론.",
        "이벤트":       "예: 6월 모의고사 대비 특강. 3주 한정 수강료 할인.",
        "기획전":       "예: 2026 영어 기획전. 독해·EBS·어법·파이널 4인 강사 통합.",
    }
    ctx = st.text_area("페이지 맥락", height=100,
                       placeholder=ph_map.get(st.session_state.purpose_type,"맥락 입력"),
                       help="강사 정보 검색 후 생성하면 더 정확한 문구가 나옵니다.")

    if st.button(f"✦ {st.session_state.purpose_type} 문구 AI 생성", type="primary", use_container_width=True):
        if not ctx.strip(): st.warning("페이지 맥락을 입력해주세요")
        elif not st.session_state.api_key: st.warning("API 키를 먼저 입력해주세요")
        else:
            with st.spinner("문구 생성 중... (10~20초)"):
                try:
                    r = gen_copy(ctx, st.session_state.purpose_type,
                                 st.session_state.target, st.session_state.purpose_label)
                    st.session_state.custom_copy = r
                    st.success("✓ 문구 생성 완료!")
                except Exception as e:
                    st.error(f"생성 실패: {e}")

    if st.session_state.custom_copy:
        st.success("✓ AI 문구 적용됨", icon="✅")
        if st.button("✕ 문구 초기화", use_container_width=True):
            st.session_state.custom_copy = None
            st.rerun()

    st.divider()

    # 섹션별 재생성
    st.markdown("### 🎲 섹션별 문구 재생성")
    st.caption("클릭 시 해당 섹션 문구만 새롭게 교체됩니다")
    regen_secs = [s for s in ordered if s in SEC_LABELS and s != "custom_section"]
    SEC_SHORT = {
        "banner":"배너","intro":"소개","why":"이유","curriculum":"커리큘럼",
        "target":"대상","reviews":"수강평","faq":"FAQ","cta":"CTA",
        "event_overview":"개요","event_benefits":"혜택","event_deadline":"마감",
        "fest_hero":"히어로","fest_lineup":"라인업","fest_benefits":"혜택","fest_cta":"CTA",
    }
    if regen_secs and st.session_state.api_key:
        for row_start in range(0, len(regen_secs), 4):
            chunk = regen_secs[row_start:row_start+4]
            cols_r = st.columns(len(chunk))
            for i, sid in enumerate(chunk):
                label = SEC_SHORT.get(sid, sid)
                with cols_r[i]:
                    if st.button(f"↺ {label}", key=f"regen_{sid}", use_container_width=True):
                        with st.spinner(f"{label} 재생성..."):
                            try:
                                r = gen_section(sid)
                                if st.session_state.custom_copy is None:
                                    st.session_state.custom_copy = {}
                                st.session_state.custom_copy.update(r)
                                st.rerun()
                            except Exception as e:
                                st.error(f"실패: {e}")
    elif not st.session_state.api_key:
        st.caption("API 키를 입력하면 활성화됩니다.")

    st.divider()

    # 문구 직접 편집
    st.markdown("### ✏️ 문구 직접 편집")
    if st.session_state.custom_copy:
        cp = st.session_state.custom_copy
        if st.session_state.purpose_type == "신규 커리큘럼":
            with st.expander("🏠 배너"):
                bt = st.text_input("메인 제목", value=cp.get("bannerTitle",""), key="ebt")
                bl = st.text_area("리드 문구", value=cp.get("bannerLead",""), height=60, key="ebl")
                cc_ = st.text_input("버튼 텍스트", value=cp.get("ctaCopy",""), key="ecc")
                if st.button("적용", key="ab"):
                    st.session_state.custom_copy.update({"bannerTitle":bt,"bannerLead":bl,"ctaCopy":cc_}); st.rerun()
            with st.expander("👤 강사 소개"):
                it = st.text_input("소개 제목", value=cp.get("introTitle",""), key="eit")
                id_ = st.text_area("소개 본문", value=cp.get("introDesc",""), height=60, key="eid")
                if st.button("적용", key="ai_"):
                    st.session_state.custom_copy.update({"introTitle":it,"introDesc":id_}); st.rerun()
        with st.expander("📣 CTA"):
            ctk = "festCtaTitle" if st.session_state.purpose_type=="기획전" else "ctaTitle"
            csk = "festCtaSub"   if st.session_state.purpose_type=="기획전" else "ctaSub"
            ct_ = st.text_area("CTA 제목", value=cp.get(ctk,""), height=60, key="ect")
            cs_ = st.text_input("서브문구", value=cp.get(csk,""), key="ecs")
            if st.button("적용", key="ac"):
                st.session_state.custom_copy.update({ctk:ct_,csk:cs_}); st.rerun()
    else:
        st.caption("AI로 문구를 생성하면 여기서 직접 수정할 수 있습니다.")

    st.divider()

    # HTML 내보내기
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

with R:
    st.markdown("### 👁 실시간 미리보기")
    td = (st.session_state.custom_theme.get("name","AI 커스텀")
          if st.session_state.concept=="custom" and st.session_state.custom_theme
          else THEMES.get(st.session_state.concept,{}).get("label",""))
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("컨셉", td)
    with m2: st.metric("히어로", T_now.get("heroStyle","—"))
    with m3: st.metric("섹션 수", len(ordered))
    import streamlit.components.v1 as components
    components.html(final_html, height=900, scrolling=True)
