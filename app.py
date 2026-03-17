import streamlit as st
import requests
import json, re, time, random

st.set_page_config(
    page_title="강사 페이지 빌더 Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state 초기화 (최우선) ──
_DEFAULTS = {
    "api_key": "",
    "concept": "sakura",
    "custom_theme": None,
    "instructor_name": "",
    "subject": "영어",
    "purpose_label": "2026 수능 파이널 완성",
    "purpose_type": "신규 커리큘럼",
    "target": "고3·N수",
    "custom_copy": None,
    "active_sections": ["banner","intro","why","curriculum","cta"],
    "ai_mood": "",
    "inst_profile": None,
    "last_seed": None,
    "custom_section_topic": "",
    "custom_section_on": False,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Secrets 자동 로드
if not st.session_state.api_key:
    try:
        st.session_state.api_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass

# ── 상수 ──
# Groq — 완전 무료, 카드 불필요 (console.groq.com)
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS  = ["llama-3.3-70b-versatile", "llama3-70b-8192", "mixtral-8x7b-32768"]

THEMES = {
    "sakura":  {"label":"🌸 벚꽃 봄",    "dark":False,
        "fonts":"https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;700&display=swap",
        "vars":"--c1:#B5304A;--c2:#E89BB5;--c3:#F5CEDA;--c4:#2A111A;--bg:#FBF6F4;--bg2:#F7EFF1;--bg3:#F2E5E9;--text:#2A111A;--t70:rgba(42,17,26,.7);--t45:rgba(42,17,26,.45);--bd:rgba(42,17,26,.10);--fh:'Playfair Display','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:12px;--r-btn:100px;",
        "extra_css":".st{font-style:italic}","cta":"linear-gradient(135deg,#2A111A,#B5304A)"},
    "fire":    {"label":"🔥 다크 파이어", "dark":True,
        "fonts":"https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@400;700;900&family=DM+Sans:wght@300;400;700&display=swap",
        "vars":"--c1:#FF4500;--c2:#FF8C00;--c3:#FFD700;--c4:#0D0705;--bg:#0D0705;--bg2:#130A04;--bg3:#1A0E06;--text:#F1F5F9;--t70:rgba(241,245,249,.7);--t45:rgba(241,245,249,.45);--bd:rgba(255,69,0,.22);--fh:'Bebas Neue','Noto Sans KR',sans-serif;--fb:'DM Sans','Noto Sans KR',sans-serif;--r:4px;--r-btn:4px;",
        "extra_css":".st{letter-spacing:.05em;text-shadow:0 0 20px rgba(255,69,0,.35)}","cta":"linear-gradient(135deg,#0D0705,#FF4500 60%,#FF8C00)"},
    "ocean":   {"label":"🌊 오션 블루",   "dark":False,
        "fonts":"https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap",
        "vars":"--c1:#0EA5E9;--c2:#38BDF8;--c3:#BAE6FD;--c4:#0C4A6E;--bg:#F0F9FF;--bg2:#E0F2FE;--bg3:#BAE6FD;--text:#0C1A2E;--t70:rgba(12,26,46,.7);--t45:rgba(12,26,46,.45);--bd:rgba(14,165,233,.15);--fh:'Syne','Noto Sans KR',sans-serif;--fb:'Noto Sans KR',sans-serif;--r:10px;--r-btn:100px;",
        "extra_css":".st{font-weight:800}","cta":"linear-gradient(135deg,#0C4A6E,#0EA5E9)"},
    "luxury":  {"label":"✨ 골드 럭셔리", "dark":True,
        "fonts":"https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,500;0,600;1,300;1,500&family=Noto+Serif+KR:wght@300;400;600&family=DM+Sans:wght@300;400;500&display=swap",
        "vars":"--c1:#C8975A;--c2:#D4AF72;--c3:#EDD8A4;--c4:#0C0B09;--bg:#0C0B09;--bg2:#131108;--bg3:#1A1810;--text:#F5F0E8;--t70:rgba(245,240,232,.7);--t45:rgba(245,240,232,.45);--bd:rgba(200,151,90,.15);--fh:'Cormorant Garamond','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:2px;--r-btn:2px;",
        "extra_css":".st{font-weight:300;font-style:italic}","cta":"linear-gradient(135deg,#0C0B09,#2A2010)"},
    "eco":     {"label":"🌿 에코 그린",   "dark":False,
        "fonts":"https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;500;700&display=swap",
        "vars":"--c1:#059669;--c2:#34D399;--c3:#A7F3D0;--c4:#064E3B;--bg:#F0FDF4;--bg2:#DCFCE7;--bg3:#BBF7D0;--text:#064E3B;--t70:rgba(6,78,59,.7);--t45:rgba(6,78,59,.45);--bd:rgba(5,150,105,.15);--fh:'DM Serif Display','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:14px;--r-btn:100px;",
        "extra_css":".st{font-style:italic}","cta":"linear-gradient(135deg,#064E3B,#059669)"},
    "winter":  {"label":"❄️ 윈터 스노우", "dark":False,
        "fonts":"https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,600;0,700;0,800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap",
        "vars":"--c1:#1E40AF;--c2:#3B82F6;--c3:#BFDBFE;--c4:#0F172A;--bg:#F8FAFF;--bg2:#EFF6FF;--bg3:#DBEAFE;--text:#0F172A;--t70:rgba(15,23,42,.7);--t45:rgba(15,23,42,.45);--bd:rgba(30,64,175,.12);--fh:'Plus Jakarta Sans','Noto Sans KR',sans-serif;--fb:'Plus Jakarta Sans','Noto Sans KR',sans-serif;--r:8px;--r-btn:100px;",
        "extra_css":".st{font-weight:800}","cta":"linear-gradient(135deg,#1E3A8A,#3B82F6)"},
    "cosmos":  {"label":"🌌 코스모스",    "dark":True,
        "fonts":"https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Noto+Sans+KR:wght@300;400;700&family=DM+Sans:wght@300;400;500&display=swap",
        "vars":"--c1:#7C3AED;--c2:#06B6D4;--c3:#A78BFA;--c4:#030712;--bg:#030712;--bg2:#080C18;--bg3:#0D1220;--text:#F1F5F9;--t70:rgba(241,245,249,.7);--t45:rgba(241,245,249,.45);--bd:rgba(124,58,237,.22);--fh:'Orbitron','Noto Sans KR',sans-serif;--fb:'DM Sans','Noto Sans KR',sans-serif;--r:0px;--r-btn:0px;",
        "extra_css":".st{letter-spacing:.12em;text-transform:uppercase}","cta":"linear-gradient(135deg,#030712,#2D1B69)"},
}

PURPOSE_SECTIONS = {
    "신규 커리큘럼": ["banner","intro","why","curriculum","target","reviews","faq","cta"],
    "이벤트":       ["banner","event_overview","event_benefits","event_deadline","reviews","cta"],
    "기획전":       ["fest_hero","fest_lineup","fest_benefits","fest_cta"],
}
PURPOSE_HINTS = {
    "신규 커리큘럼": "📚 강사 전문성·신뢰감 강조 — 골드 럭셔리, 코스모스, 윈터 추천",
    "이벤트":       "🎉 기간 한정·긴박감·혜택 강조 — 벚꽃, 에코, 파이어 추천",
    "기획전":       "🏆 강사 라인업·규모감·통합 혜택 강조 — 파이어, 코스모스, 골드 추천",
}
SECTION_LABELS = {
    "banner":"🏠 메인 배너","intro":"👤 강사 소개","why":"💡 이유","curriculum":"📚 커리큘럼",
    "target":"🎯 수강 대상","reviews":"⭐ 수강평","faq":"❓ FAQ","cta":"📣 수강신청 CTA",
    "event_overview":"📅 이벤트 개요","event_benefits":"🎁 이벤트 혜택","event_deadline":"⏰ 마감 안내",
    "fest_hero":"🏆 기획전 히어로","fest_lineup":"👥 강사 라인업","fest_benefits":"🎁 기획전 혜택","fest_cta":"📣 기획전 CTA",
    "custom_section":"✏️ 기타 (직접 입력)",
}
RANDOM_SEEDS = [
    {"mood":"사이버펑크 보라 네온사인, 비오는 다크 도시","layout":"brutalist","font":"display"},
    {"mood":"고대 이집트 황금 신전, 사막 모래와 오벨리스크","layout":"editorial","font":"serif"},
    {"mood":"북유럽 스칸디나비아 미니멀, 하얀 안개 자작나무 숲","layout":"minimal","font":"sans"},
    {"mood":"수험생 새벽 4시 형광등 책상, 집중과 고요","layout":"brutalist","font":"mono"},
    {"mood":"극지방 오로라 청록 보라 새벽하늘","layout":"immersive","font":"display"},
    {"mood":"빈티지 옥스퍼드 도서관, 가죽 책 양피지","layout":"magazine","font":"serif"},
    {"mood":"다크 아카데미아 빅토리안 고딕 도서관","layout":"editorial","font":"serif"},
    {"mood":"오래된 수학 교실 분필 칠판 먼지 냄새","layout":"editorial","font":"mono"},
    {"mood":"겨울 새벽 눈 덮인 사찰 고요 집중 먹빛","layout":"minimal","font":"serif"},
    {"mood":"여름 밤 루프탑 바, 도시 스카이라인 인디고","layout":"immersive","font":"display"},
    {"mood":"19세기 파리 아방가르드 예술 포스터","layout":"magazine","font":"display"},
    {"mood":"네온 팝아트 비비드 원색 90s 리트로","layout":"brutalist","font":"display"},
    {"mood":"미래 우주선 내부 홀로그램 테크 UI","layout":"immersive","font":"mono"},
    {"mood":"흑백 필름 사진관, 빈티지 모노크롬","layout":"minimal","font":"mono"},
    {"mood":"그리스 지중해 흰 건물 코발트 블루 바다","layout":"modern","font":"sans"},
    {"mood":"마젠타 핫핑크 와일드 패션 하이패션","layout":"brutalist","font":"display"},
    {"mood":"무채색 모더니즘 건축 차가운 강철 콘크리트","layout":"brutalist","font":"sans"},
    {"mood":"가을 단풍 교정 은행나무, 따뜻한 주황 갈색","layout":"organic","font":"serif"},
    {"mood":"사파이어 새벽 플라네타리움 별빛 금빛","layout":"immersive","font":"display"},
    {"mood":"관중이 가득찬 야구장, 밤의 전광판 붉은빛","layout":"brutalist","font":"display"},
]
SUBJECT_KW = {
    "영어":["빈칸 추론","EBS 연계","순서·삽입","어법·어휘"],
    "수학":["수1·수2","미적분","확률과 통계","킬러 문항"],
    "국어":["독해력","문학","비문학","화법과 작문"],
    "사회":["생활과 윤리","한국지리","세계사","경제"],
    "과학":["물리학","화학","생명과학","지구과학"],
}

# ── AI 호출 (REST API 직접 — SDK 없음) ──
def call_gemini(prompt, system="", json_mode=True, max_tokens=3000):
    """Groq API 호출 — 완전 무료, 카드 불필요"""
    key = st.session_state.api_key.strip()
    if not key:
        raise ValueError("API 키가 없습니다. 사이드바에서 gsk_... 키를 입력해주세요.")

    messages = []
    sys_parts = []
    if system:
        sys_parts.append(system)
    if json_mode:
        sys_parts.append("Return ONLY valid JSON. No markdown fences. No extra text.")
    if sys_parts:
        messages.append({"role": "system", "content": "\n\n".join(sys_parts)})
    messages.append({"role": "user", "content": prompt})

    last_err = None
    for model in GROQ_MODELS:
        try:
            resp = requests.post(
                GROQ_API_URL,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages,
                      "max_tokens": max_tokens, "temperature": 0.7},
                timeout=60,
            )
        except Exception as e:
            last_err = Exception(f"네트워크 오류: {e}"); continue

        if resp.status_code == 401:
            raise Exception("🔑 API 키 오류 — console.groq.com에서 키를 확인해주세요.")
        if resp.status_code == 429:
            last_err = Exception(f"⏳ 한도 초과 ({model}) — 잠시 후 재시도")
            time.sleep(2); continue
        if resp.status_code in (400, 404):
            try: msg = resp.json().get("error", {}).get("message", "")
            except Exception: msg = resp.text[:100]
            last_err = Exception(f"HTTP {resp.status_code} ({model}): {msg}"); continue
        if not resp.ok:
            try: msg = resp.json().get("error", {}).get("message", resp.text[:150])
            except Exception: msg = resp.text[:150]
            last_err = Exception(f"HTTP {resp.status_code} ({model}): {msg}"); continue

        try:
            text = resp.json()["choices"][0]["message"]["content"]
            if text and text.strip():
                return text
            last_err = Exception(f"응답 비어있음 ({model})"); continue
        except (KeyError, IndexError) as e:
            last_err = Exception(f"응답 파싱 실패 ({model}): {e}"); continue

    raise last_err or Exception("모든 모델 실패 — API 키를 확인해주세요.")


def gen_concept(seed):
    lg = {"brutalist":"sharp corners 0-2px, heavy uppercase, stark contrast",
          "editorial":"large serif italic, generous whitespace, asymmetric 2-col",
          "minimal":"extreme whitespace, thin weights, almost no decoration",
          "magazine":"mixed font sizes, editorial grid",
          "immersive":"full-bleed dark, glowing accents, dramatic contrast",
          "organic":"rounded 16-24px, blob shapes, natural tones",
          "modern":"clean grid, 8-12px radius, confident sans-serif",
          "mono":"monospace, terminal aesthetic",
          "geometric":"bauhaus, primary colors"}.get(seed.get("layout","auto"),"choose best fit")
    fg = {"serif":"Playfair Display or Cormorant Garamond",
          "sans":"Syne or Plus Jakarta Sans",
          "display":"Bebas Neue or Abril Fatface",
          "mono":"IBM Plex Mono or Space Mono",
          "auto":"choose boldly to match mood"}.get(seed.get("font","auto"),"choose boldly")
    return safe_json(call_gemini(
        f"""한국 교육 랜딩페이지 UI/UX 디자이너.
무드: "{seed['mood']}" | 레이아웃: {seed.get("layout","auto")} — {lg} | 폰트: {fg}

규칙:
- extraCSS: 최소 150자, clip-path/box-shadow/text-shadow/background-image/transform 적극 사용
- extraCSS 내부는 반드시 작은따옴표(') 사용 (큰따옴표 절대 금지)
- particle: petals=벚꽃봄만, embers=불꽃, snow=겨울, stars=우주, gold=황금, leaves=자연, 나머지=none
- 모든 값 한 줄 (줄바꿈 없음)

다음 JSON만 반환:
{{"name":"2-4한글+이모지","dark":true,"c1":"#hex","c2":"#hex","c3":"#hex","c4":"#hex","bg":"#hex","bg2":"#hex","bg3":"#hex","textHex":"#hex","textRgb":"r,g,b","bdAlpha":"rgba(r,g,b,.12)","displayFont":"Google Font","bodyFont":"Noto Sans KR","fontWeights":"400;700;900","displayFontWeights":"400;700","borderRadiusPx":8,"btnBorderRadiusPx":100,"particle":"none","ctaGradient":"linear-gradient(135deg,#hex,#hex)","extraCSS":"min 150 chars single quotes only"}}""",
        "Return ONLY valid compact JSON. extraCSS must use single quotes only."))

def gen_copy(ctx, ptype, name, subj, tgt, plabel):
    schemas = {
        "신규 커리큘럼": '{"bannerSub":"8자","bannerTitle":"15자","bannerLead":"40자","ctaCopy":"8자","ctaTitle":"CTA제목","ctaSub":"25자","ctaBadge":"15자","statBadges":[["수치","라벨"],["수치","라벨"],["수치","라벨"]],"introTitle":"15자","introDesc":"60자","introBio":"40자","introBadges":[["수치","라벨"],["수치","라벨"],["수치","라벨"]],"whyTitle":"15자","whySub":"25자","whyReasons":[["이모지","10자","40자"],["이모지","10자","40자"],["이모지","10자","40자"]],"curriculumTitle":"20자","curriculumSub":"25자","curriculumSteps":[["01","7자","12자","기간"],["02","제목","설명","기간"],["03","제목","설명","기간"],["04","제목","설명","기간"]],"targetTitle":"15자","targetItems":["항목","항목","항목","항목"],"reviews":[["인용문25자","이름","뱃지"],["인용문","이름","뱃지"],["인용문","이름","뱃지"]],"faqs":[["질문12자","답변35자"],["질문","답변"],["질문","답변"]]}',
        "이벤트": '{"bannerSub":"8자","bannerTitle":"15자","bannerLead":"40자","ctaCopy":"8자","ctaTitle":"CTA제목","ctaSub":"25자","ctaBadge":"15자","statBadges":[["수치","라벨"],["수치","라벨"],["수치","라벨"]],"eventTitle":"이벤트제목20자","eventDesc":"설명40자","eventDetails":[["📅","이벤트 기간","날짜"],["🎯","대상","값"],["💰","할인율","값"]],"benefitsTitle":"혜택제목20자","eventBenefits":[{"icon":"이모지","title":"혜택명","desc":"설명35자","badge":"뱃지8자","no":"01"},{"icon":"이모지","title":"혜택명","desc":"설명","badge":"뱃지","no":"02"},{"icon":"이모지","title":"혜택명","desc":"설명","badge":"뱃지","no":"03"}],"deadlineTitle":"마감제목20자","deadlineMsg":"마감메시지60자","reviews":[["인용문","이름","뱃지"],["인용문","이름","뱃지"],["인용문","이름","뱃지"]]}',
        "기획전": '{"festHeroTitle":"기획전제목20자","festHeroCopy":"서브카피30자","festHeroSub":"설명40자","festHeroStats":[["수치","라벨"],["수치","라벨"],["수치","라벨"],["수치","라벨"]],"festLineupTitle":"라인업제목20자","festLineupSub":"설명40자","festLineup":[{"name":"강사명","tag":"분야8자","tagline":"한줄소개30자","badge":"뱃지8자","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"소개","badge":"뱃지","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"소개","badge":"뱃지","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"소개","badge":"뱃지","emoji":"이모지"}],"festBenefitsTitle":"혜택제목20자","festBenefits":[{"icon":"이모지","title":"혜택명","desc":"설명35자","badge":"뱃지8자","no":"01"},{"icon":"이모지","title":"혜택명","desc":"설명","badge":"뱃지","no":"02"},{"icon":"이모지","title":"혜택명","desc":"설명","badge":"뱃지","no":"03"},{"icon":"이모지","title":"혜택명","desc":"설명","badge":"뱃지","no":"04"}],"festCtaTitle":"CTA제목줄바꿈은<br>","festCtaSub":"서브문구40자"}',
    }
    inst = f"강사: {name} {subj}." if name else ""
    return safe_json(call_gemini(
        f"""한국어 교육 마케팅 카피라이터.
맥락: "{ctx}" | 목적: {ptype} | 과목: {subj} | 대상: {tgt} | 브랜드: {plabel}
{inst}
목적별 강조 — 신규 커리큘럼:전문성·체계·신뢰 / 이벤트:기간한정·긴박감·혜택 / 기획전:라인업·규모·통합혜택
JSON만 반환 (마크다운 없이, 값에 줄바꿈 없이): {schemas.get(ptype, schemas['신규 커리큘럼'])}""",
        "한국어 교육 카피라이터. 유효한 JSON만 반환.", max_tokens=4000))
def gen_custom_section(topic, subj, name, purpose_label):
    """기타 섹션 AI 생성 — 사용자 입력 토픽에 맞게"""
    inst = f"강사: {name}." if name else ""
    return safe_json(call_gemini(
        f"""한국어 교육 랜딩페이지 카피라이터.
섹션 주제: "{topic}"
과목: {subj} | 브랜드: {purpose_label}
{inst}

주제에 맞는 섹션 내용을 생성하라. 수강평 이벤트, 특별 혜택, 합격 후기, 학습 팁, 공지사항 등 어떤 주제든 자유롭게.

다음 JSON만 반환 (마크다운 없이, 줄바꿈 없이):
{{"tag":"섹션 태그(8자이내)","title":"섹션 제목(20자이내)","desc":"설명 문구(60자이내, items가 없을 때만 표시)","items":[{{"icon":"이모지","title":"항목 제목(15자이내)","desc":"항목 설명(45자이내)"}},{{"icon":"이모지","title":"항목 제목","desc":"항목 설명"}},{{"icon":"이모지","title":"항목 제목","desc":"항목 설명"}}]}}

항목이 있는 경우 desc는 빈 문자열로.""",
        "Korean education copywriter. Return ONLY valid JSON.", max_tokens=1500))



# ── 테마 리졸버 ──
def get_theme():
    if st.session_state.concept == "custom" and st.session_state.custom_theme:
        ct = st.session_state.custom_theme
        df = ct.get("displayFont","Noto Sans KR")
        bf = ct.get("bodyFont","Noto Sans KR")
        fw = ct.get("fontWeights","400;700;900")
        dfw = ct.get("displayFontWeights","400;700")
        r = ct.get("borderRadiusPx",8)
        rb = ct.get("btnBorderRadiusPx",100)
        tr = ct.get("textRgb","255,255,255")
        bd = ct.get("bdAlpha","rgba(255,255,255,.12)")
        fonts = (f"https://fonts.googleapis.com/css2?family={df.replace(' ','+')}:wght@{dfw}"
                 f"&family={bf.replace(' ','+')}:wght@{fw}&display=swap")
        vars_ = (f"--c1:{ct['c1']};--c2:{ct['c2']};--c3:{ct['c3']};--c4:{ct['c4']};"
                 f"--bg:{ct['bg']};--bg2:{ct['bg2']};--bg3:{ct['bg3']};"
                 f"--text:{ct['textHex']};--t70:rgba({tr},.7);--t45:rgba({tr},.45);"
                 f"--bd:{bd};--fh:'{df}','Noto Serif KR',serif;"
                 f"--fb:'{bf}',sans-serif;--r:{r}px;--r-btn:{rb}px;")
        return {"fonts":fonts,"vars":vars_,"extra_css":ct.get("extraCSS",""),
                "dark":ct.get("dark",True),"cta":ct.get("ctaGradient",f"linear-gradient(135deg,{ct['c4']},{ct['c1']})")}
    t = THEMES.get(st.session_state.concept, THEMES["sakura"])
    return {"fonts":t["fonts"],"vars":t["vars"],"extra_css":t.get("extra_css",""),
            "dark":t.get("dark",False),"cta":t.get("cta","linear-gradient(135deg,var(--c4),var(--c1))")}

# ── Base CSS ──
BASE_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:var(--fb);background:var(--bg);color:var(--text);overflow-x:hidden;-webkit-font-smoothing:antialiased}
a{text-decoration:none;color:inherit}
.rv{opacity:0;transform:translateY(18px);transition:opacity .85s cubic-bezier(.16,1,.3,1),transform .85s cubic-bezier(.16,1,.3,1)}
.rv.on{opacity:1;transform:none}
.d1{transition-delay:.1s}.d2{transition-delay:.22s}.d3{transition-delay:.35s}
@keyframes up{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
.btn-p{display:inline-flex;align-items:center;gap:7px;background:var(--c1);color:#fff;font-family:var(--fb);font-size:14px;font-weight:700;padding:13px 30px;border-radius:var(--r-btn,100px);border:none;cursor:pointer;box-shadow:0 4px 18px rgba(0,0,0,.18);transition:opacity .15s,transform .15s;text-decoration:none}
.btn-p:hover{opacity:.88;transform:translateY(-1px)}
.btn-s{display:inline-flex;align-items:center;gap:7px;background:transparent;color:var(--text);font-family:var(--fb);font-size:14px;font-weight:600;padding:12px 22px;border-radius:var(--r-btn,100px);border:1.5px solid var(--bd);cursor:pointer;transition:border-color .15s;text-decoration:none}
.btn-s:hover{border-color:var(--c1);color:var(--c1)}
.sec{padding:clamp(52px,7vw,80px) clamp(24px,6vw,70px)}
.sec.alt{background:var(--bg2)}
.tag-line{display:inline-flex;align-items:center;gap:8px;font-size:9.5px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--c1);margin-bottom:13px}
.tag-line::before{content:'';display:block;width:20px;height:1px;background:var(--c1)}
.sec-h2{font-family:var(--fh);font-size:clamp(24px,3.8vw,36px);font-weight:700;line-height:1.2;letter-spacing:-.03em;color:var(--text);margin-bottom:11px}
.sec-sub{font-size:14px;line-height:1.95;color:var(--t70);margin-bottom:36px;max-width:540px}
.card{background:var(--bg);border:1px solid var(--bd);border-radius:var(--r,12px);padding:22px;transition:transform .2s,box-shadow .2s}
.card:hover{transform:translateY(-3px);box-shadow:0 8px 28px rgba(0,0,0,.09)}
.st{}
"""

# ── 섹션 빌더 ──
def sec_banner(d,cp,T):
    sub=cp.get("bannerSub",d["subject"]+" 완성"); title=cp.get("bannerTitle",d["purpose_label"]); lead=cp.get("bannerLead",f"{d['target']}을 위한 최강 커리큘럼"); cta=cp.get("ctaCopy","수강신청하기")
    stats=cp.get("statBadges",[["98%","수강 만족도"],["1,200+","합격생"],["15년+","강의 경력"]]); kws=SUBJECT_KW.get(d["subject"],["개념","기출","실전","파이널"])
    sh="".join(f'<div><div style="font-family:var(--fh);font-size:clamp(20px,3vw,28px);font-weight:900;color:var(--c1)">{sv}</div><div style="font-size:9px;color:var(--t45);font-weight:600;letter-spacing:.1em;text-transform:uppercase;margin-top:2px">{sl}</div></div>' for sv,sl in stats)
    kh="".join(f'<span style="font-size:9.5px;font-weight:700;padding:5px 12px;border-radius:var(--r-btn,100px);color:var(--c1);border:1px solid var(--bd)">{k}</span>' for k in kws)
    inst=f'<div style="display:inline-flex;align-items:center;gap:8px;margin-top:20px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:4px;padding:6px 14px"><span style="font-size:11px;color:var(--t45)">{d["name"]} 선생님</span></div>' if d["name"] else ""
    db="rgba(255,255,255,.03)" if T["dark"] else "var(--bg3)"
    ci="".join(f'<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid var(--bd)"><span style="font-size:11px;color:var(--t45);font-weight:600">{l}</span><span style="font-size:11.5px;font-weight:700">{v}</span></div>' for l,v in [["강의 대상",d["target"]],["과목",d["subject"]],["목적",d["purpose_label"][:12]+"…"]])
    return f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;background:var(--bg);display:grid;grid-template-columns:1fr 380px"><div style="position:relative;z-index:2;display:flex;flex-direction:column;justify-content:center;padding:clamp(60px,8vw,100px) clamp(24px,4vw,52px) clamp(60px,8vw,100px) clamp(32px,6vw,88px)"><div style="display:flex;align-items:center;gap:10px;margin-bottom:32px"><div style="width:24px;height:1.5px;background:var(--c1)"></div><span style="font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:var(--c1)">{sub}</span></div><h1 style="font-family:var(--fh);font-size:clamp(44px,6.5vw,90px);font-weight:900;line-height:.88;letter-spacing:-.05em;color:var(--text)" class="st">{title}</h1><p style="font-size:clamp(13px,1.4vw,15.5px);line-height:2.05;color:var(--t70);margin-top:24px;max-width:400px;padding-left:14px;border-left:2px solid var(--c2)">{lead}</p><div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:20px">{kh}</div>{inst}<div style="display:flex;gap:12px;margin-top:30px"><a class="btn-p" href="#">{cta} →</a><a class="btn-s" href="#">강의 미리보기</a></div><div style="display:flex;gap:28px;margin-top:52px;padding-top:28px;border-top:1px solid var(--bd)">{sh}</div></div><div style="background:{db};border-left:1px solid var(--bd);display:flex;align-items:center;justify-content:center;padding:52px 28px"><div style="width:100%;background:{"rgba(255,255,255,.05)" if T["dark"] else "var(--bg)"};border:1px solid var(--bd);border-radius:var(--r,12px);overflow:hidden"><div style="background:var(--c1);padding:20px 24px;text-align:center"><div style="font-family:var(--fh);font-size:22px;font-weight:900;color:#fff">{title}</div></div><div style="padding:20px 24px">{ci}<a class="btn-p" href="#" style="width:100%;justify-content:center;margin-top:16px;display:flex">{cta} →</a></div></div></div></section>'

def sec_intro(d,cp,T):
    t=cp.get("introTitle",f"{d['name']} 선생님 소개"); desc=cp.get("introDesc",f"{d['subject']} 최상위권 합격의 비결"); bio=cp.get("introBio","압도적인 합격 실적으로 검증된 강의력")
    badges=cp.get("introBadges",[["98%","수강 만족도"],["1,200+","합격생 수"],["15년+","강의 경력"],["#1","과목 랭킹"]])
    bh="".join(f'<div style="text-align:center;padding:16px;border:1px solid var(--bd);border-radius:var(--r,10px)"><div style="font-family:var(--fh);font-size:22px;font-weight:900;color:var(--c1)">{bv}</div><div style="font-size:9px;color:var(--t45);font-weight:600;letter-spacing:.1em;text-transform:uppercase;margin-top:3px">{bl}</div></div>' for bv,bl in badges)
    return f'<section class="sec alt" id="intro"><div class="rv"><div class="tag-line">강사 소개</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{desc}</p></div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px" class="rv d1">{bh}</div><div style="margin-top:20px;padding:16px 20px;border-left:3px solid var(--c1);background:var(--bg3);border-radius:0 var(--r,8px) var(--r,8px) 0" class="rv d2"><p style="font-size:13px;line-height:1.9;color:var(--t70)">{bio}</p></div></section>'

def sec_why(d,cp,T):
    t=cp.get("whyTitle","이 강의가 필요한 이유"); s=cp.get("whySub",f"{d['subject']} 1등급의 비결")
    reasons=cp.get("whyReasons",[["🎯","유형별 완전 정복","수능 출제 유형을 완전히 분석하여 어떤 문제도 흔들리지 않는 실력을 만듭니다."],["📊","데이터 기반 학습","10년간의 기출 데이터를 분석하여 효율적으로 학습합니다."],["⚡","실전 속도 훈련","정확도와 속도를 동시에 잡아 실전 완벽 대비합니다."]])
    rh="".join(f'<div class="card"><div style="display:flex;align-items:center;gap:12px;margin-bottom:14px"><div style="width:44px;height:44px;border-radius:var(--r,12px);background:var(--c1);display:flex;align-items:center;justify-content:center;font-size:20px">{ic}</div><div style="font-family:var(--fh);font-size:15px;font-weight:700" class="st">{tt}</div></div><p style="font-size:13px;line-height:1.85;color:var(--t70)">{dc}</p></div>' for ic,tt,dc in reasons)
    return f'<section class="sec" id="why"><div class="rv"><div class="tag-line">수강 이유</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{s}</p></div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px" class="rv d1">{rh}</div></section>'

def sec_curriculum(d,cp,T):
    t=cp.get("curriculumTitle",f"{d['purpose_label']} 커리큘럼"); s=cp.get("curriculumSub","체계적인 4단계 완성 로드맵")
    steps=cp.get("curriculumSteps",[["01","개념 완성","핵심 개념 정리","4주"],["02","유형 훈련","기출 완전 분석","4주"],["03","심화 특훈","고난도 완전 정복","4주"],["04","파이널","실전 마무리","4주"]])
    sh="".join(f'<div class="card" style="position:relative;overflow:hidden"><div style="position:absolute;top:-12px;right:-8px;font-family:var(--fh);font-size:80px;font-weight:900;color:var(--c1);opacity:.05;line-height:1">{no}</div><div style="font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--c1);margin-bottom:8px">STEP {no}</div><div style="font-family:var(--fh);font-size:16px;font-weight:700;margin-bottom:6px" class="st">{tt}</div><div style="font-size:12px;color:var(--t70);margin-bottom:8px">{dc}</div><span style="font-size:10px;background:var(--c1);color:#fff;padding:3px 10px;border-radius:100px;font-weight:700">{du}</span></div>' for no,tt,dc,du in steps)
    return f'<section class="sec alt" id="curriculum"><div class="rv"><div class="tag-line">커리큘럼</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{s}</p></div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px" class="rv d1">{sh}</div></section>'

def sec_target(d,cp,T):
    t=cp.get("targetTitle","이런 분들께 추천합니다")
    items=cp.get("targetItems",[f"수능까지 {d['subject']} 점수를 확실히 올리고 싶은 분","개념은 아는데 실전 점수가 안 나오는 분","N수를 준비하며 전략적 커리큘럼이 필요한 분",f"{d['subject']} 상위권 도약을 위한 마지막 기회를 찾는 분"])
    ih="".join(f'<div class="card" style="display:flex;align-items:center;gap:13px;padding:16px 20px"><div style="width:26px;height:26px;min-width:26px;border-radius:50%;background:var(--c1);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;color:#fff">{i+1}</div><span style="font-size:14px;font-weight:500">{txt}</span></div>' for i,txt in enumerate(items))
    return f'<section class="sec" id="target"><div class="rv"><div class="tag-line">수강 대상</div><h2 class="sec-h2 st">{t}</h2></div><div style="display:flex;flex-direction:column;gap:8px" class="rv d1">{ih}</div></section>'

def sec_reviews(d,cp,T):
    reviews=cp.get("reviews",[[f'"{d["subject"]}가 이렇게 재밌는 과목이었나요? 성적도 오르고 자신감도 생겼어요!"',"고3 김OO","1등급 달성"],['"개념부터 실전까지 빈틈없는 커리큘럼."',"N수 이OO","2→1등급"],[f'"선생님 덕분에 {d["subject"]}의 구조가 보이기 시작했어요."',"고2 박OO","내신 3→1등급"]])
    rh="".join(f'<div class="card" style="display:flex;flex-direction:column;gap:10px"><div style="color:#F59E0B;font-size:11px">★★★★★</div><p style="font-size:13px;line-height:1.85;font-weight:500">{txt}</p><div style="display:flex;align-items:center;justify-content:space-between;padding-top:10px;border-top:1px solid var(--bd)"><span style="font-size:11px;color:var(--t45)">— {nm} 학생</span><span style="font-size:10px;background:var(--bg3);color:var(--c1);padding:3px 10px;border-radius:100px;font-weight:700;border:1px solid var(--bd)">{badge}</span></div></div>' for txt,nm,badge in reviews)
    return f'<section class="sec alt" id="reviews"><div class="rv"><div class="tag-line">수강평</div><h2 class="sec-h2 st">생생한 수강생 후기</h2></div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px" class="rv d1">{rh}</div></section>'

def sec_faq(d,cp,T):
    faqs=cp.get("faqs",[["수강 기간은 얼마나 되나요?","기본 30일이며, 연장권으로 최대 90일 가능합니다."],["교재는 별도 구매인가요?","별도 구매이며, 신청 페이지에서 함께 구매하실 수 있습니다."],["모바일에서도 수강 가능한가요?","PC와 모바일 모두 가능합니다."]])
    fh="".join(f'<div style="border:1px solid var(--bd);border-radius:var(--r,10px);overflow:hidden;margin-bottom:6px"><div style="padding:13px 17px;background:var(--bg3);display:flex;gap:9px"><span style="color:var(--c1);font-weight:800;font-size:14px;flex-shrink:0">Q</span><span style="font-weight:600;font-size:13px">{q}</span></div><div style="padding:12px 17px;background:var(--bg);display:flex;gap:9px"><span style="color:var(--t45);font-weight:700;font-size:14px;flex-shrink:0">A</span><span style="font-size:13px;line-height:1.75;color:var(--t70)">{a}</span></div></div>' for q,a in faqs)
    return f'<section class="sec" id="faq"><div class="rv"><div class="tag-line">FAQ</div><h2 class="sec-h2 st">자주 묻는 질문</h2></div><div class="rv d1">{fh}</div></section>'

def sec_cta(d,cp,T):
    tt=cp.get("ctaTitle",f"지금 바로 시작해<br>{d['subject']} 1등급을 확보하세요"); sub=cp.get("ctaSub",f"{d['name']} 선생님과 함께라면 가능합니다."); cc=cp.get("ctaCopy","지금 수강신청하기"); badge=cp.get("ctaBadge",f"{d['target']} 전용")
    return f'<section style="padding:clamp(64px,9vw,100px) clamp(24px,6vw,72px);text-align:center;position:relative;overflow:hidden;background:{T["cta"]}"><div style="position:absolute;top:-100px;right:-100px;width:400px;height:400px;border-radius:50%;background:rgba(255,255,255,.04);pointer-events:none"></div><div style="position:relative;z-index:1"><div style="display:inline-block;background:rgba(255,255,255,.10);padding:5px 16px;border-radius:100px;font-size:10px;font-weight:700;color:#fff;margin-bottom:18px">{badge}</div><h2 style="font-family:var(--fh);font-size:clamp(26px,4.5vw,48px);font-weight:900;line-height:1.15;letter-spacing:-.03em;color:#fff;margin-bottom:12px">{tt}</h2><p style="color:rgba(255,255,255,.65);font-size:15px;margin-bottom:36px">{sub}</p><div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap"><a style="display:inline-flex;align-items:center;gap:7px;background:#fff;color:#0A0A0A;font-weight:800;padding:14px 40px;border-radius:100px;font-size:15px;text-decoration:none" href="#">{cc} →</a><a style="display:inline-flex;align-items:center;gap:7px;background:transparent;color:rgba(255,255,255,.8);font-weight:600;padding:13px 28px;border-radius:100px;border:1.5px solid rgba(255,255,255,.3);font-size:14px;text-decoration:none" href="#">카카오톡 문의</a></div></div></section>'

def sec_event_overview(d,cp,T):
    t=cp.get("eventTitle",d["purpose_label"]); desc=cp.get("eventDesc","이 이벤트는 기간 한정으로 진행됩니다.")
    details=cp.get("eventDetails",[["📅","이벤트 기간","2026년 4월 1일 — 4월 30일"],["🎯","대상","고3·N수"],["💰","할인율","최대 30%"]])
    dh="".join(f'<div class="card" style="text-align:center;padding:28px 20px"><div style="font-size:32px;margin-bottom:12px">{ic}</div><div style="font-size:11px;font-weight:700;color:var(--c1);letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px">{lb}</div><div style="font-family:var(--fh);font-size:18px;font-weight:700;font-style:italic">{vl}</div></div>' for ic,lb,vl in details)
    return f'<section class="sec" id="event-overview"><div class="rv"><div class="tag-line">이벤트 개요</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{desc}</p></div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px" class="rv d1">{dh}</div></section>'

def sec_event_benefits(d,cp,T):
    t=cp.get("benefitsTitle","이벤트 특별 혜택")
    benefits=cp.get("eventBenefits",[{"icon":"🎁","title":"수강료 특가","desc":"이벤트 기간 최대 30% 할인.","badge":"최대 30%","no":"01"},{"icon":"📚","title":"교재 무료 제공","desc":"핵심 교재가 무료로 제공됩니다.","badge":"무료 제공","no":"02"},{"icon":"🔥","title":"라이브 특강","desc":"매주 토요일 라이브 특강 무료.","badge":"매주 토요일","no":"03"}])
    bh="".join(f'<div class="card" style="display:grid;grid-template-columns:60px 1fr;gap:18px;align-items:flex-start;padding:22px"><div style="width:60px;height:60px;border-radius:var(--r,14px);background:linear-gradient(135deg,var(--c1),var(--c2));display:flex;align-items:center;justify-content:center;font-size:26px;flex-shrink:0">{b["icon"]}</div><div><div style="display:flex;align-items:center;gap:7px;margin-bottom:7px"><span style="font-size:9px;font-weight:800;color:var(--c1);opacity:.7">NO.{b["no"]}</span><span style="background:var(--c1);color:#fff;font-size:9px;font-weight:700;padding:2px 9px;border-radius:100px">{b["badge"]}</span></div><div style="font-family:var(--fh);font-size:15px;font-weight:700;margin-bottom:7px" class="st">{b["title"]}</div><p style="font-size:12px;line-height:1.82;color:var(--t70)">{b["desc"]}</p></div></div>' for b in benefits)
    return f'<section class="sec alt" id="event-benefits"><div class="rv"><div class="tag-line">이벤트 혜택</div><h2 class="sec-h2 st">{t}</h2></div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px" class="rv d1">{bh}</div></section>'

def sec_event_deadline(d,cp,T):
    t=cp.get("deadlineTitle","마감 안내 / 타임라인"); msg=cp.get("deadlineMsg","이벤트는 기간 한정으로 운영됩니다."); cc=cp.get("ctaCopy","이벤트 신청하기")
    return f'<section class="sec" id="event-deadline" style="background:{T["cta"]};text-align:center"><div class="rv"><div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.15);padding:6px 20px;border-radius:100px;font-size:11px;font-weight:700;color:#fff;margin-bottom:24px">⏰ 마감 안내</div><h2 style="font-family:var(--fh);font-size:clamp(24px,3.5vw,40px);font-weight:900;color:#fff;margin-bottom:16px" class="st">{t}</h2><p style="color:rgba(255,255,255,.7);font-size:15px;line-height:1.8;margin-bottom:36px;max-width:480px;margin-left:auto;margin-right:auto">{msg}</p><a style="display:inline-flex;align-items:center;gap:7px;background:#fff;color:#0A0A0A;font-weight:800;padding:14px 48px;border-radius:100px;font-size:16px;text-decoration:none" href="#">{cc} →</a></div></section>'

def sec_fest_hero(d,cp,T):
    t=cp.get("festHeroTitle",f"{d['subject']} 기획전"); cc=cp.get("festHeroCopy","최고의 강사들이 한 자리에"); sub=cp.get("festHeroSub",f"수능 {d['subject']} 전 강사 라인업.")
    stats=cp.get("festHeroStats",[["4인","강사 라인업"],["30%","통합 할인"],["1,200+","누적 합격"],["#1","과목 랭킹"]])
    sh="".join(f'<div style="text-align:center"><div style="font-family:var(--fh);font-size:clamp(20px,3vw,32px);font-weight:900;color:var(--c1)">{sv}</div><div style="font-size:9px;color:rgba(255,255,255,.5);font-weight:600;letter-spacing:.1em;text-transform:uppercase;margin-top:3px">{sl}</div></div>' for sv,sl in stats)
    return f'<section id="fest-hero" style="position:relative;min-height:80vh;overflow:hidden;background:{T["cta"]};display:flex;flex-direction:column;justify-content:center;text-align:center;padding:clamp(80px,10vw,120px) clamp(28px,6vw,80px)"><div style="position:absolute;inset:0;background:radial-gradient(ellipse 80% 70% at 50% 30%,rgba(255,255,255,.08),transparent 65%);pointer-events:none"></div><div style="position:relative;z-index:2"><div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.12);backdrop-filter:blur(8px);padding:6px 20px;border-radius:100px;font-size:11px;font-weight:700;color:#fff;margin-bottom:24px;border:1px solid rgba(255,255,255,.2)">🏆 {d["subject"]} 기획전</div><h1 style="font-family:var(--fh);font-size:clamp(40px,7vw,100px);font-weight:900;line-height:.85;letter-spacing:-.05em;color:#fff;margin-bottom:20px" class="st">{t}</h1><p style="font-size:clamp(18px,2.5vw,24px);color:rgba(255,255,255,.75);margin-bottom:12px;font-weight:700">{cc}</p><p style="font-size:15px;color:rgba(255,255,255,.55);margin-bottom:48px;max-width:500px;margin-left:auto;margin-right:auto">{sub}</p><div style="display:flex;gap:48px;justify-content:center;flex-wrap:wrap;padding-top:40px;border-top:1px solid rgba(255,255,255,.15)">{sh}</div></div></section>'

def sec_fest_lineup(d,cp,T):
    t=cp.get("festLineupTitle","강사 라인업"); s=cp.get("festLineupSub",f"{d['subject']} 전 영역 최강 강사진")
    lineup=cp.get("festLineup",[{"name":"강사A","tag":"독해·문법","tagline":"수능 영어 독해의 정석","badge":"베스트셀러","emoji":"📖"},{"name":"강사B","tag":"EBS 연계","tagline":"EBS 연계율 100% 완벽 적중","badge":"적중률 1위","emoji":"🎯"},{"name":"강사C","tag":"어법·어휘","tagline":"어법·어휘 전문 빠른 풀이","badge":"속도UP","emoji":"⚡"},{"name":"강사D","tag":"파이널","tagline":"수능 D-30 파이널 완성","badge":"파이널 특화","emoji":"🏆"}])
    lh="".join(f'<div class="card" style="text-align:center;padding:28px 20px"><div style="font-size:40px;margin-bottom:14px">{l["emoji"]}</div><div style="display:inline-flex;align-items:center;gap:6px;background:var(--bg3);color:var(--c1);font-size:9px;font-weight:700;padding:4px 12px;border-radius:100px;margin-bottom:12px;border:1px solid var(--bd)">{l["tag"]}</div><div style="font-family:var(--fh);font-size:18px;font-weight:900;margin-bottom:8px" class="st">{l["name"]}</div><p style="font-size:12px;line-height:1.7;color:var(--t70);margin-bottom:12px">{l["tagline"]}</p><span style="font-size:10px;background:var(--c1);color:#fff;padding:4px 14px;border-radius:100px;font-weight:700">{l["badge"]}</span></div>' for l in lineup)
    return f'<section class="sec alt" id="fest-lineup"><div class="rv"><div class="tag-line">강사 라인업</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{s}</p></div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px" class="rv d1">{lh}</div></section>'

def sec_fest_benefits(d,cp,T):
    t=cp.get("festBenefitsTitle","기획전 특별 혜택")
    benefits=cp.get("festBenefits",[{"icon":"🎁","title":"전 강사 통합 수강료 특가","desc":"최대 30% 추가 할인.","badge":"최대 30%","no":"01"},{"icon":"📚","title":"통합 학습 자료 무료 제공","desc":"통합 교재 및 기출 자료 무료.","badge":"무료 제공","no":"02"},{"icon":"🔥","title":"주간 라이브 특강","desc":"매주 전 강사 참여 라이브.","badge":"전 강사 참여","no":"03"},{"icon":"🏆","title":"목표 등급 보장","desc":"목표 등급 미달성 시 재수강.","badge":"성적 보장","no":"04"}])
    bh="".join(f'<div class="card" style="display:grid;grid-template-columns:60px 1fr;gap:18px;align-items:flex-start;padding:22px"><div style="width:60px;height:60px;border-radius:var(--r,14px);background:linear-gradient(135deg,var(--c1),var(--c2));display:flex;align-items:center;justify-content:center;font-size:26px;flex-shrink:0">{b["icon"]}</div><div><div style="display:flex;align-items:center;gap:7px;margin-bottom:7px"><span style="font-size:9px;font-weight:800;color:var(--c1);opacity:.7">NO.{b["no"]}</span><span style="background:var(--c1);color:#fff;font-size:9px;font-weight:700;padding:2px 9px;border-radius:100px">{b["badge"]}</span></div><div style="font-family:var(--fh);font-size:15px;font-weight:700;margin-bottom:7px" class="st">{b["title"]}</div><p style="font-size:12px;line-height:1.82;color:var(--t70)">{b["desc"]}</p></div></div>' for b in benefits)
    return f'<section class="sec" id="fest-benefits"><div class="rv"><div class="tag-line">기획전 혜택</div><h2 class="sec-h2 st">{t}</h2></div><div style="display:grid;grid-template-columns:repeat(2,1fr);gap:16px" class="rv d1">{bh}</div></section>'

def sec_fest_cta(d,cp,T):
    t=cp.get("festCtaTitle",f"지금 바로 {d['subject']} 기획전<br>전체 강사 라인업을 만나세요"); s=cp.get("festCtaSub",f"최고의 강사들과 함께 {d['subject']} 1등급 완성.")
    return f'<section style="padding:clamp(64px,9vw,104px) clamp(24px,6vw,72px);text-align:center;position:relative;overflow:hidden;background:{T["cta"]}"><div style="position:absolute;top:-120px;left:50%;transform:translateX(-50%);width:700px;height:700px;border-radius:50%;background:rgba(255,255,255,.03);pointer-events:none"></div><div style="position:relative;z-index:1"><div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.12);backdrop-filter:blur(8px);padding:6px 20px;border-radius:100px;font-size:11px;font-weight:700;color:#fff;margin-bottom:24px;border:1px solid rgba(255,255,255,.2)">🏆 {d["subject"]} 기획전 통합 신청</div><h2 style="font-family:var(--fh);font-size:clamp(28px,4.8vw,56px);font-weight:900;line-height:1.08;letter-spacing:-.03em;color:#fff;margin-bottom:16px">{t}</h2><p style="color:rgba(255,255,255,.62);font-size:15px;line-height:1.75;margin-bottom:42px;max-width:480px;margin-left:auto;margin-right:auto">{s}</p><div style="display:flex;gap:13px;justify-content:center;flex-wrap:wrap"><a style="display:inline-flex;align-items:center;gap:8px;background:#fff;color:#0A0A0A;font-weight:800;padding:17px 48px;border-radius:100px;font-size:16px;text-decoration:none" href="#">기획전 통합 신청 →</a><a style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.1);backdrop-filter:blur(8px);color:rgba(255,255,255,.82);font-weight:600;padding:16px 30px;border-radius:100px;border:1.5px solid rgba(255,255,255,.3);font-size:14px;text-decoration:none" href="#">강사 개별 신청</a></div></div></section>'


def sec_custom(d, cp, T):
    """기타 섹션 — 사용자가 제목을 입력하면 AI가 내용 생성"""
    c = cp.get("custom_section_data", {})
    if not c:
        return ""
    tag   = c.get("tag",   "추가 안내")
    title = c.get("title", "추가 섹션")
    items = c.get("items", [])
    desc  = c.get("desc",  "")
    items_html = "".join(
        f'<div class="card" style="padding:20px 22px">'
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">'
        f'<div style="width:36px;height:36px;min-width:36px;border-radius:50%;background:var(--c1);display:flex;align-items:center;justify-content:center;font-size:16px">{it.get("icon","✦")}</div>'
        f'<div style="font-family:var(--fh);font-size:14px;font-weight:700" class="st">{it.get("title","")}</div></div>'
        f'<p style="font-size:12.5px;line-height:1.85;color:var(--t70)">{it.get("desc","")}</p></div>'
        for it in items
    ) if items else f'<p style="font-size:14px;line-height:1.9;color:var(--t70)">{desc}</p>'
    cols = "repeat(3,1fr)" if len(items) >= 3 else ("repeat(2,1fr)" if len(items) == 2 else "1fr")
    grid_or_p = f'<div style="display:grid;grid-template-columns:{cols};gap:12px" class="rv d1">{items_html}</div>' if items else f'<div class="rv d1">{items_html}</div>'
    return f'<section class="sec" id="custom-section"><div class="rv"><div class="tag-line">{tag}</div><h2 class="sec-h2 st">{title}</h2></div>{grid_or_p}</section>'

# ── HTML 빌더 ──
def build_html(secs):
    T = get_theme()
    cp = st.session_state.custom_copy or {}
    d = {"name":st.session_state.instructor_name or "","subject":st.session_state.subject,
         "purpose_label":st.session_state.purpose_label,"target":st.session_state.target}
    dc = ".card{background:var(--bg2)!important}" if T["dark"] else ""
    mp = {"banner":sec_banner,"intro":sec_intro,"why":sec_why,"curriculum":sec_curriculum,
          "target":sec_target,"reviews":sec_reviews,"faq":sec_faq,"cta":sec_cta,
          "event_overview":sec_event_overview,"event_benefits":sec_event_benefits,"event_deadline":sec_event_deadline,
          "fest_hero":sec_fest_hero,"fest_lineup":sec_fest_lineup,"fest_benefits":sec_fest_benefits,"fest_cta":sec_fest_cta,
          "custom_section":sec_custom}
    body = "\n".join(mp[s](d,cp,T) for s in secs if s in mp)
    ttl = cp.get("bannerTitle", cp.get("festHeroTitle", d["purpose_label"]))
    return (f'<!DOCTYPE html>\n<html lang="ko"><head><meta charset="UTF-8"/>'
            f'<meta name="viewport" content="width=device-width,initial-scale=1.0"/>'
            f'<title>{d["name"]} {d["subject"]} · {ttl}</title>'
            f'<link rel="preconnect" href="https://fonts.googleapis.com"/>'
            f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>'
            f'<link href="{T["fonts"]}" rel="stylesheet"/>'
            f'<style>:root{{{T["vars"]}}}{BASE_CSS}{T["extra_css"]}{dc}</style>'
            f'</head><body>{body}'
            f'<script>const ro=new IntersectionObserver(es=>{{es.forEach(e=>{{if(e.isIntersecting){{e.target.classList.add("on");ro.unobserve(e.target);}}}});}},{{threshold:.06}});document.querySelectorAll(".rv").forEach(el=>ro.observe(el));</script>'
            f'</body></html>')

# ── Streamlit CSS ──
st.markdown("""<style>
[data-testid="stSidebar"]{background:#0A0D14;}
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,[data-testid="stSidebar"] span{color:#C8D4EA!important;}
.stButton>button{border-radius:8px;font-weight:700;width:100%;transition:opacity .15s;}
div[data-testid="stMetric"]{background:#0B0F1C;border:1px solid #1E2640;border-radius:8px;padding:12px;}
</style>""", unsafe_allow_html=True)

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("### 🎓 강사 페이지 빌더 Pro")
    st.caption("컨셉별 프리미엄 랜딩페이지 생성기")
    st.divider()

    # API Key
    st.markdown("**🔑 Groq API Key** ([무료 발급 →](https://console.groq.com))")
    _secret_key = ""
    try:
        _secret_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass
    if _secret_key and not st.session_state.api_key:
        st.session_state.api_key = _secret_key
    if _secret_key and st.session_state.api_key == _secret_key:
        st.success("✓ Secrets에서 자동 로드됨", icon="🔒")
    else:
        api_in = st.text_input("API Key", type="password", value=st.session_state.api_key,
                               placeholder="gsk_...", label_visibility="collapsed")
        if api_in != st.session_state.api_key:
            st.session_state.api_key = api_in
        if st.session_state.api_key:
            st.success("✓ Groq API 키 입력됨 (완전 무료!)", icon="✅")
        else:
            st.info("👆 console.groq.com → API Keys → Create API Key", icon="🔑")

    st.divider()

    # 페이지 목적
    st.markdown("**📋 페이지 목적**")
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
    st.markdown("**🎨 페이지 컨셉**")
    if st.button("🎲 AI 랜덤 생성 — 누를 때마다 완전히 새 디자인!", use_container_width=True, type="primary"):
        if not st.session_state.api_key:
            st.warning("API 키를 먼저 입력해주세요")
        else:
            seed = random.choice(RANDOM_SEEDS)
            while len(RANDOM_SEEDS) > 1 and seed == st.session_state.last_seed:
                seed = random.choice(RANDOM_SEEDS)
            st.session_state.last_seed = seed
            with st.spinner(f"🎨 '{seed['mood'][:22]}...' 생성 중..."):
                try:
                    r = gen_concept(seed)
                    st.session_state.custom_theme = r
                    st.session_state.concept = "custom"
                    st.success(f"✓ '{r.get('name','새 컨셉')}' 생성! 다시 눌러서 또 바꿔보세요.")
                    st.rerun()
                except Exception as e:
                    st.error(f"생성 실패: {e}")

    st.caption("20가지 무드 중 랜덤 · 매번 다른 폰트·컬러·CSS 구조")
    st.markdown("또는 직접 묘사:")
    mood_in = st.text_area("무드", height=65,
        placeholder="예: 사이버펑크 네온사인 다크 도시\n예: 고대 이집트 황금 신전 사막",
        value=st.session_state.ai_mood, label_visibility="collapsed")
    st.session_state.ai_mood = mood_in
    if st.button("✦ 이 무드로 생성", use_container_width=True):
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
                    st.success(f"✓ '{r.get('name','새 컨셉')}' 생성됨!")
                    st.rerun()
                except Exception as e:
                    st.error(f"생성 실패: {e}")

    st.markdown("또는 프리셋:")
    c1_, c2_ = st.columns(2)
    for i, (k, t) in enumerate(THEMES.items()):
        with (c1_ if i % 2 == 0 else c2_):
            if st.button(t["label"], key=f"th_{k}",
                         type="primary" if st.session_state.concept == k else "secondary",
                         use_container_width=True):
                st.session_state.concept = k
                st.session_state.custom_theme = None
                st.rerun()
    if st.session_state.concept == "custom" and st.session_state.custom_theme:
        ct = st.session_state.custom_theme
        st.success(f"✦ 현재: {ct.get('name','AI 커스텀')}")

    st.divider()

    # 강사 정보
    st.markdown("**👤 강사 정보**")
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
        if not nm:
            st.warning("강사명을 먼저 입력해주세요")
        elif not st.session_state.api_key:
            st.warning("API 키를 먼저 입력해주세요")
        else:
            with st.spinner(f"{nm} 선생님 정보 검색 중..."):
                try:
                    p = safe_json(call_gemini(
                        f'Find Korean 수능 educator "{nm}" teaching "{sb}". '
                        f'Return ONLY JSON: {{"found":true,"bio":"2-3 sentences","slogan":"motto or empty","signatureMethods":["method"],"desc":"value prop"}}',
                        "Korean education researcher. Return ONLY valid compact JSON."))
                    st.session_state.inst_profile = p
                    if p.get("found"):
                        st.success("✓ 강사 정보 검색 완료!")
                    else:
                        st.info("정보를 찾지 못했습니다.")
                except Exception as e:
                    st.error(f"검색 실패: {e}")

    st.divider()

    # 설정
    st.markdown("**📝 강의 브랜드명**")
    pl = st.text_input("브랜드명", value=st.session_state.purpose_label,
                       placeholder="2026 수능 파이널 완성", label_visibility="collapsed")
    st.session_state.purpose_label = pl

    st.markdown("**🎯 수강 대상**")
    tgt = st.radio("대상", ["고3·N수","고1·2 — 기초 완성"],
                   horizontal=True, label_visibility="collapsed")
    st.session_state.target = tgt

    st.divider()

    # 섹션
    st.markdown("**📑 섹션 ON/OFF**")
    for sid in PURPOSE_SECTIONS[st.session_state.purpose_type]:
        chk = st.checkbox(SECTION_LABELS.get(sid, sid),
                          value=sid in st.session_state.active_sections, key=f"sec_{sid}")
        if chk and sid not in st.session_state.active_sections:
            st.session_state.active_sections.append(sid)
        elif not chk and sid in st.session_state.active_sections:
            st.session_state.active_sections.remove(sid)

    # ── 기타(직접 입력) 섹션 ──
    st.markdown("---")
    custom_on = st.checkbox("✏️ 기타 (직접 입력) 섹션 추가",
                            value=st.session_state.custom_section_on, key="chk_custom")
    st.session_state.custom_section_on = custom_on
    if custom_on:
        if "custom_section" not in st.session_state.active_sections:
            st.session_state.active_sections.append("custom_section")
        topic_in = st.text_input(
            "섹션 주제 입력",
            value=st.session_state.custom_section_topic,
            placeholder="예: 수강평 이벤트, 합격 후기, 특별 혜택, 공지사항",
            label_visibility="collapsed",
            key="custom_topic_inp",
        )
        st.session_state.custom_section_topic = topic_in
        if st.button("✦ AI로 섹션 생성", use_container_width=True, key="gen_custom_sec"):
            if not topic_in.strip():
                st.warning("섹션 주제를 입력해주세요")
            elif not st.session_state.api_key:
                st.warning("API 키를 먼저 입력해주세요")
            else:
                with st.spinner(f"'{topic_in}' 섹션 생성 중..."):
                    try:
                        result = gen_custom_section(
                            topic_in,
                            st.session_state.subject,
                            st.session_state.instructor_name,
                            st.session_state.purpose_label,
                        )
                        if st.session_state.custom_copy is None:
                            st.session_state.custom_copy = {}
                        st.session_state.custom_copy["custom_section_data"] = result
                        st.success(f"✓ '{result.get('title','섹션')}' 생성됨!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"생성 실패: {e}")
        if st.session_state.custom_copy and st.session_state.custom_copy.get("custom_section_data"):
            d_cs = st.session_state.custom_copy["custom_section_data"]
            st.caption(f"현재: {d_cs.get('title','—')} ({len(d_cs.get('items',[]))}개 항목)")
    else:
        if "custom_section" in st.session_state.active_sections:
            st.session_state.active_sections.remove("custom_section")

# ── MAIN ──
ordered = [s for s in PURPOSE_SECTIONS[st.session_state.purpose_type]
           if s in st.session_state.active_sections]
final_html = build_html(ordered)

L, R = st.columns([1, 2], gap="large")

with L:
    st.markdown(f"### ✍️ AI 문구 생성")
    st.caption(PURPOSE_HINTS[st.session_state.purpose_type])
    ph_map = {
        "신규 커리큘럼": "예: 2026 수능 영어 파이널 완성. 고3·N수 대상. 김철수 선생님, ABPS 방법론.",
        "이벤트":       "예: 6월 모의고사 대비 특강. 3주 한정. 수강료 30% 할인.",
        "기획전":       "예: 2026 영어 기획전. 독해·EBS·어법·파이널 4인 강사 통합 패키지.",
    }
    ctx = st.text_area("페이지 맥락", height=100,
                       placeholder=ph_map.get(st.session_state.purpose_type, "맥락 입력"),
                       help="AI가 목적에 맞는 문구를 생성합니다.")
    if st.button(f"✦ {st.session_state.purpose_type} 문구 AI 생성", type="primary", use_container_width=True):
        if not ctx.strip():
            st.warning("페이지 맥락을 입력해주세요")
        elif not st.session_state.api_key:
            st.warning("API 키를 먼저 입력해주세요")
        else:
            with st.spinner(f"{st.session_state.purpose_type} 맞춤 문구 생성 중... (10~20초)"):
                try:
                    r = gen_copy(ctx, st.session_state.purpose_type,
                                 st.session_state.instructor_name, st.session_state.subject,
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
    st.markdown("### ✏️ 문구 직접 편집")
    if st.session_state.custom_copy:
        cp = st.session_state.custom_copy
        if st.session_state.purpose_type == "신규 커리큘럼":
            with st.expander("배너"):
                bt = st.text_input("메인 제목", value=cp.get("bannerTitle",""), key="ebt")
                bl = st.text_area("리드 문구", value=cp.get("bannerLead",""), height=55, key="ebl")
                cc_ = st.text_input("버튼 텍스트", value=cp.get("ctaCopy",""), key="ecc")
                if st.button("배너 적용", key="ab"):
                    st.session_state.custom_copy.update({"bannerTitle":bt,"bannerLead":bl,"ctaCopy":cc_})
                    st.rerun()
            with st.expander("강사 소개"):
                it = st.text_input("소개 제목", value=cp.get("introTitle",""), key="eit")
                id_ = st.text_area("소개 본문", value=cp.get("introDesc",""), height=55, key="eid")
                if st.button("소개 적용", key="ai_"):
                    st.session_state.custom_copy.update({"introTitle":it,"introDesc":id_})
                    st.rerun()
        elif st.session_state.purpose_type == "이벤트":
            with st.expander("이벤트 개요"):
                etl = st.text_input("이벤트 제목", value=cp.get("eventTitle",""), key="eetl")
                edesc = st.text_area("이벤트 설명", value=cp.get("eventDesc",""), height=55, key="eedesc")
                if st.button("이벤트 적용", key="aev"):
                    st.session_state.custom_copy.update({"eventTitle":etl,"eventDesc":edesc})
                    st.rerun()
        elif st.session_state.purpose_type == "기획전":
            with st.expander("기획전 히어로"):
                fht = st.text_input("기획전 제목", value=cp.get("festHeroTitle",""), key="efht")
                fhc = st.text_input("서브 카피", value=cp.get("festHeroCopy",""), key="efhc")
                if st.button("기획전 적용", key="afh"):
                    st.session_state.custom_copy.update({"festHeroTitle":fht,"festHeroCopy":fhc})
                    st.rerun()
        ctk = "festCtaTitle" if st.session_state.purpose_type == "기획전" else "ctaTitle"
        csk = "festCtaSub"   if st.session_state.purpose_type == "기획전" else "ctaSub"
        with st.expander("CTA"):
            ct_ = st.text_area("CTA 제목", value=cp.get(ctk,""), height=55, key="ect")
            cs_ = st.text_input("서브문구", value=cp.get(csk,""), key="ecs")
            if st.button("CTA 적용", key="ac"):
                st.session_state.custom_copy.update({ctk:ct_, csk:cs_})
                st.rerun()
    else:
        st.caption("AI로 문구를 생성하면 여기서 직접 수정할 수 있습니다.")

    st.divider()
    st.markdown("### 📥 HTML 내보내기")
    cn = (st.session_state.custom_theme.get("name","custom")
          if st.session_state.concept == "custom" and st.session_state.custom_theme
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
    T_data = get_theme()
    td = (st.session_state.custom_theme.get("name","AI 커스텀")
          if st.session_state.concept == "custom" and st.session_state.custom_theme
          else THEMES.get(st.session_state.concept,{}).get("label",""))
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("컨셉", td)
    with m2: st.metric("목적", st.session_state.purpose_type)
    with m3: st.metric("섹션 수", len(ordered))
    import streamlit.components.v1 as components
    components.html(final_html, height=900, scrolling=True)
