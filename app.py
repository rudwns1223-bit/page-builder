"""
강사 페이지 빌더 Pro v6
- Groq API (완전 무료, 카드 불필요)
- 배경 이미지 자동 생성 (loremflickr)
- 한자 자동 제거
- 강사별 고유 내용 생성
"""
import streamlit as st
import requests
import json, re, time, random, unicodedata

st.set_page_config(
    page_title="강사 페이지 빌더 Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════
# SESSION STATE 초기화 (최우선)
# ══════════════════════════════════════
_D = {
    "api_key": "", "concept": "sakura", "custom_theme": None,
    "instructor_name": "", "subject": "영어",
    "purpose_label": "2026 수능 파이널 완성",
    "purpose_type": "신규 커리큘럼", "target": "고3·N수",
    "custom_copy": None, "bg_photo_url": "",
    "active_sections": ["banner","intro","why","curriculum","cta"],
    "ai_mood": "", "inst_profile": None, "last_seed": None,
    "custom_section_on": False, "custom_section_topic": "",
}
for _k, _v in _D.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Streamlit Secrets 자동 로드
if not st.session_state.api_key:
    try:
        st.session_state.api_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        pass

# ══════════════════════════════════════
# 상수
# ══════════════════════════════════════
GROQ_URL    = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama3-70b-8192", "mixtral-8x7b-32768"]

THEMES = {
    "sakura": {"label":"🌸 벚꽃 봄","dark":False,
        "fonts":"https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;700&display=swap",
        "vars":"--c1:#B5304A;--c2:#E89BB5;--c3:#F5CEDA;--c4:#2A111A;--bg:#FBF6F4;--bg2:#F7EFF1;--bg3:#F2E5E9;--text:#2A111A;--t70:rgba(42,17,26,.7);--t45:rgba(42,17,26,.45);--bd:rgba(42,17,26,.10);--fh:'Playfair Display','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:12px;--r-btn:100px;",
        "extra_css":".st{font-style:italic}","cta":"linear-gradient(135deg,#2A111A,#B5304A)","heroStyle":"editorial"},
    "fire":   {"label":"🔥 다크 파이어","dark":True,
        "fonts":"https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@400;700;900&family=DM+Sans:wght@300;400;700&display=swap",
        "vars":"--c1:#FF4500;--c2:#FF8C00;--c3:#FFD700;--c4:#0D0705;--bg:#0D0705;--bg2:#130A04;--bg3:#1A0E06;--text:#F1F5F9;--t70:rgba(241,245,249,.7);--t45:rgba(241,245,249,.45);--bd:rgba(255,69,0,.22);--fh:'Bebas Neue','Noto Sans KR',sans-serif;--fb:'DM Sans','Noto Sans KR',sans-serif;--r:4px;--r-btn:4px;",
        "extra_css":".st{letter-spacing:.05em}","cta":"linear-gradient(135deg,#0D0705,#FF4500 60%,#FF8C00)","heroStyle":"immersive"},
    "ocean":  {"label":"🌊 오션 블루","dark":False,
        "fonts":"https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap",
        "vars":"--c1:#0EA5E9;--c2:#38BDF8;--c3:#BAE6FD;--c4:#0C4A6E;--bg:#F0F9FF;--bg2:#E0F2FE;--bg3:#BAE6FD;--text:#0C1A2E;--t70:rgba(12,26,46,.7);--t45:rgba(12,26,46,.45);--bd:rgba(14,165,233,.15);--fh:'Syne','Noto Sans KR',sans-serif;--fb:'Noto Sans KR',sans-serif;--r:10px;--r-btn:100px;",
        "extra_css":".st{font-weight:800}","cta":"linear-gradient(135deg,#0C4A6E,#0EA5E9)","heroStyle":"split"},
    "luxury": {"label":"✨ 골드 럭셔리","dark":True,
        "fonts":"https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,500;0,600;1,300;1,500&family=Noto+Serif+KR:wght@300;400;600&family=DM+Sans:wght@300;400;500&display=swap",
        "vars":"--c1:#C8975A;--c2:#D4AF72;--c3:#EDD8A4;--c4:#0C0B09;--bg:#0C0B09;--bg2:#131108;--bg3:#1A1810;--text:#F5F0E8;--t70:rgba(245,240,232,.7);--t45:rgba(245,240,232,.45);--bd:rgba(200,151,90,.15);--fh:'Cormorant Garamond','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:2px;--r-btn:2px;",
        "extra_css":".st{font-weight:300;font-style:italic}","cta":"linear-gradient(135deg,#0C0B09,#2A2010)","heroStyle":"editorial"},
    "eco":    {"label":"🌿 에코 그린","dark":False,
        "fonts":"https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;500;700&display=swap",
        "vars":"--c1:#059669;--c2:#34D399;--c3:#A7F3D0;--c4:#064E3B;--bg:#F0FDF4;--bg2:#DCFCE7;--bg3:#BBF7D0;--text:#064E3B;--t70:rgba(6,78,59,.7);--t45:rgba(6,78,59,.45);--bd:rgba(5,150,105,.15);--fh:'DM Serif Display','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:14px;--r-btn:100px;",
        "extra_css":".st{font-style:italic}","cta":"linear-gradient(135deg,#064E3B,#059669)","heroStyle":"split"},
    "winter": {"label":"❄️ 윈터 스노우","dark":False,
        "fonts":"https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,600;0,700;0,800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap",
        "vars":"--c1:#1E40AF;--c2:#3B82F6;--c3:#BFDBFE;--c4:#0F172A;--bg:#F8FAFF;--bg2:#EFF6FF;--bg3:#DBEAFE;--text:#0F172A;--t70:rgba(15,23,42,.7);--t45:rgba(15,23,42,.45);--bd:rgba(30,64,175,.12);--fh:'Plus Jakarta Sans','Noto Sans KR',sans-serif;--fb:'Plus Jakarta Sans','Noto Sans KR',sans-serif;--r:8px;--r-btn:100px;",
        "extra_css":".st{font-weight:800}","cta":"linear-gradient(135deg,#1E3A8A,#3B82F6)","heroStyle":"split"},
    "cosmos": {"label":"🌌 코스모스","dark":True,
        "fonts":"https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Noto+Sans+KR:wght@300;400;700&family=DM+Sans:wght@300;400;500&display=swap",
        "vars":"--c1:#7C3AED;--c2:#06B6D4;--c3:#A78BFA;--c4:#030712;--bg:#030712;--bg2:#080C18;--bg3:#0D1220;--text:#F1F5F9;--t70:rgba(241,245,249,.7);--t45:rgba(241,245,249,.45);--bd:rgba(124,58,237,.22);--fh:'Orbitron','Noto Sans KR',sans-serif;--fb:'DM Sans','Noto Sans KR',sans-serif;--r:0px;--r-btn:0px;",
        "extra_css":".st{letter-spacing:.1em;text-transform:uppercase}","cta":"linear-gradient(135deg,#030712,#2D1B69)","heroStyle":"immersive"},
}

PURPOSE_SECTIONS = {
    "신규 커리큘럼": ["banner","intro","why","curriculum","target","reviews","faq","cta"],
    "이벤트":       ["banner","event_overview","event_benefits","event_deadline","reviews","cta"],
    "기획전":       ["fest_hero","fest_lineup","fest_benefits","fest_cta"],
}
PURPOSE_HINTS = {
    "신규 커리큘럼": "📚 강사 전문성·신뢰감 강조 — 골드, 코스모스, 윈터 추천",
    "이벤트":       "🎉 기간 한정·긴박감·혜택 강조 — 벚꽃, 에코, 파이어 추천",
    "기획전":       "🏆 강사 라인업·통합 혜택 강조 — 파이어, 코스모스, 골드 추천",
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
    {"mood":"사이버펑크 보라 네온사인, 비오는 다크 도시","layout":"brutalist","font":"display"},
    {"mood":"고대 이집트 황금 신전, 사막 모래와 오벨리스크","layout":"editorial","font":"serif"},
    {"mood":"북유럽 스칸디나비아 미니멀, 하얀 안개 자작나무 숲","layout":"minimal","font":"sans"},
    {"mood":"수험생 새벽 4시 형광등 책상, 집중과 고요","layout":"brutalist","font":"mono"},
    {"mood":"극지방 오로라 청록 보라 새벽하늘","layout":"immersive","font":"display"},
    {"mood":"빈티지 옥스퍼드 도서관, 가죽 책 양피지","layout":"magazine","font":"serif"},
    {"mood":"다크 아카데미아 빅토리안 고딕 도서관","layout":"editorial","font":"serif"},
    {"mood":"관중이 가득찬 야구장, 밤의 전광판 붉은빛","layout":"brutalist","font":"display"},
    {"mood":"오래된 수학 교실 분필 칠판 먼지 냄새","layout":"editorial","font":"mono"},
    {"mood":"겨울 새벽 눈 덮인 사찰 고요 집중 먹빛","layout":"minimal","font":"serif"},
    {"mood":"여름 밤 루프탑 바, 도시 스카이라인 인디고","layout":"immersive","font":"display"},
    {"mood":"19세기 파리 아방가르드 예술 포스터","layout":"magazine","font":"display"},
    {"mood":"네온 팝아트 비비드 원색 90s 리트로","layout":"brutalist","font":"display"},
    {"mood":"미래 우주선 내부 홀로그램 테크 UI","layout":"immersive","font":"mono"},
    {"mood":"그리스 지중해 흰 건물 코발트 블루 바다","layout":"modern","font":"sans"},
    {"mood":"가을 단풍 교정 은행나무, 따뜻한 주황 갈색","layout":"organic","font":"serif"},
    {"mood":"흑백 필름 사진관, 빈티지 모노크롬","layout":"minimal","font":"mono"},
    {"mood":"마젠타 핫핑크 와일드 패션 하이패션","layout":"brutalist","font":"display"},
    {"mood":"사파이어 새벽 플라네타리움 별빛 금빛","layout":"immersive","font":"display"},
    {"mood":"무채색 모더니즘 건축 차가운 강철 콘크리트","layout":"brutalist","font":"sans"},
]
SUBJ_KW = {
    "영어":["빈칸 추론","EBS 연계","순서·삽입","어법·어휘"],
    "수학":["수1·수2","미적분","확률과 통계","킬러 문항"],
    "국어":["독해력","문학","비문학","화법과 작문"],
    "사회":["생활과 윤리","한국지리","세계사","경제"],
    "과학":["물리학","화학","생명과학","지구과학"],
}

# 배경 이미지 키워드 맵
KO_BG = {
    "관중이 가득찬 야구장": "baseball stadium crowd night lights",
    "야구장": "baseball stadium crowd night",
    "사람 많은 야구장": "baseball stadium crowd night",
    "사람많은 야구장": "baseball stadium crowd night",
    "야구": "baseball game crowd stadium",
    "경기장": "sports arena stadium crowd",
    "축구장": "soccer stadium crowd night",
    "농구장": "basketball court arena",
    "관중": "stadium crowd cheering",
    "경기장": "sports stadium arena",
    "밤": "night dark dramatic",
    "새벽": "dawn morning light",
    "도서관": "library books dark wooden",
    "책": "books library study",
    "교실": "classroom chalkboard",
    "칠판": "chalkboard chalk classroom",
    "도시": "city urban skyline",
    "우주": "space cosmos galaxy",
    "별": "stars night sky",
    "오로라": "aurora borealis northern lights",
    "바다": "ocean sea dramatic",
    "숲": "forest trees nature",
    "단풍": "autumn leaves fall",
    "벚꽃": "cherry blossom spring",
    "겨울": "winter snow cold",
    "사막": "desert sand golden",
    "이집트": "egypt pyramid desert",
    "사찰": "temple korea traditional",
    "안개": "foggy mist atmospheric",
    "네온": "neon lights city night",
    "사이버펑크": "cyberpunk neon city rain",
    "불꽃": "fire flame dramatic",
    "고딕": "gothic dark dramatic",
    "빈티지": "vintage retro film",
    "루프탑": "rooftop city skyline night",
    "자작나무": "birch forest fog minimal",
    "플라네타리움": "planetarium stars cosmos",
    "건축": "architecture brutalist concrete",
    "포스터": "art poster vintage paris",
    "댄스": "dance performance stage",
    "dancing": "dance performance stage dramatic",
    "soccer": "soccer stadium crowd night",
    "baseball": "baseball stadium crowd lights",
}

# ══════════════════════════════════════
# 유틸
# ══════════════════════════════════════
def strip_hanja(text: str) -> str:
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    result = []
    for ch in text:
        cp = ord(ch)
        if 0x4E00 <= cp <= 0x9FFF: continue
        if 0x3400 <= cp <= 0x4DBF: continue
        if 0x20000 <= cp <= 0x2A6DF: continue
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
    # 잘린 JSON 복구
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
    """한글/영어 무드 → 실사 배경 이미지 URL
    loremflickr.com: 키워드 기반 Flickr 실사 이미지 (무료, 안정적)
    """
    if not mood: return ""
    text = mood.lower()
    found = []
    # 긴 키워드부터 매칭 (가장 구체적인 표현 우선)
    for ko, en in sorted(KO_BG.items(), key=lambda x: -len(x[0])):
        if ko.lower() in text:
            found.extend(en.split())
            text = text.replace(ko.lower(), " ")
            if len(found) >= 6:
                break
    # 영어 단어 직접 사용
    eng = [w for w in re.findall(r"[a-zA-Z]{4,}", mood)
           if w.lower() not in ("this","that","with","from","have","been","just","very")]
    found.extend(eng[:3])
    if not found:
        found = ["stadium","crowd","sports","night"]
    # 중복 제거, 최대 3개 (loremflickr는 키워드가 적을수록 정확)
    tags = ",".join(list(dict.fromkeys(found))[:3])
    lock = random.randint(1, 99999)
    # loremflickr: 실제 Flickr 사진 키워드 검색 제공
    return f"https://loremflickr.com/1920/900/{tags}?lock={lock}"

# ══════════════════════════════════════
# AI 호출
# ══════════════════════════════════════
def call_ai(prompt: str, system: str = "", max_tokens: int = 2000) -> str:
    key = st.session_state.api_key.strip()
    if not key:
        raise ValueError("API 키가 없습니다. 사이드바에서 gsk_... 키를 입력해주세요.")
    messages = []
    sys_parts = [system] if system else []
    sys_parts.append("Return ONLY valid JSON. No markdown. No extra text. Never use Chinese characters (漢字). Write everything in Korean (한글) only.")
    messages.append({"role":"system","content":"\n\n".join(sys_parts)})
    messages.append({"role":"user","content":prompt})
    last_err = None
    for model in GROQ_MODELS:
        try:
            resp = requests.post(
                GROQ_URL,
                headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
                json={"model":model,"messages":messages,"max_tokens":max_tokens,"temperature":0.7},
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
        except (KeyError, IndexError) as e:
            last_err = Exception(f"응답 파싱 실패: {e}"); continue
    raise last_err or Exception("모든 모델 실패")

# ══════════════════════════════════════
# AI 생성 함수
# ══════════════════════════════════════
def gen_concept(seed: dict) -> dict:
    lg = {"brutalist":"sharp 0-2px radius, heavy uppercase, stark contrast",
          "editorial":"serif italic, generous whitespace, asymmetric 2-col",
          "minimal":"extreme whitespace, thin weights",
          "magazine":"mixed sizes, editorial grid",
          "immersive":"full-bleed dark, glowing accents",
          "organic":"rounded 16-24px, natural tones",
          "modern":"clean grid, 8-12px radius","mono":"monospace terminal",
          "geometric":"bauhaus primary"}.get(seed.get("layout","auto"),"choose best fit")
    fg = {"serif":"Playfair Display or Cormorant Garamond",
          "sans":"Syne or Plus Jakarta Sans",
          "display":"Bebas Neue or Abril Fatface",
          "mono":"IBM Plex Mono","auto":"choose boldly"}.get(seed.get("font","auto"),"choose boldly")
    prompt = f"""한국 교육 랜딩페이지 UI 디자이너.
무드: "{seed['mood']}" | 레이아웃: {seed.get("layout","auto")} — {lg} | 폰트: {fg}

규칙:
- extraCSS: 최소 120자, clip-path/box-shadow/text-shadow/transform 적극 사용
- extraCSS 내부 CSS 문자열은 반드시 작은따옴표(') 사용
- particle: petals=벚꽃봄, embers=불꽃, snow=겨울, stars=우주, gold=황금, leaves=자연, 나머지=none
- heroStyle: "split"(2컬럼), "immersive"(풀스크린), "editorial"(에디토리얼) 중 하나

다음 JSON만 반환 (한 줄, 줄바꿈 없음):
{{"name":"2-4글자+이모지(교육/한국/랜딩/페이지/수능 같은 단어 절대금지 — 무드 분위기를 담은 창의적 이름)","dark":true,"heroStyle":"immersive","c1":"#hex","c2":"#hex","c3":"#hex","c4":"#hex","bg":"#hex","bg2":"#hex","bg3":"#hex","textHex":"#hex","textRgb":"r,g,b","bdAlpha":"rgba(r,g,b,.12)","displayFont":"Google Font","bodyFont":"Noto Sans KR","fontWeights":"400;700;900","displayFontWeights":"400;700","borderRadiusPx":8,"btnBorderRadiusPx":100,"particle":"none","ctaGradient":"linear-gradient(135deg,#hex,#hex)","extraCSS":"CSS min 120 chars single quotes only"}}"""
    result = safe_json(call_ai(prompt, max_tokens=800))
    # 컨셉 이름이 너무 일반적이면 무드 기반으로 직접 생성
    name = result.get("name","")
    generic = ["한국","교육","랜딩","페이지","강사","수능","학습","공부","스터디"]
    if not name or any(g in name for g in generic) or len(name) > 12:
        # 무드 첫 단어로 컨셉명 생성
        mood_word = seed.get("mood","").split()[0][:4] if seed.get("mood") else "새 컨셉"
        result["name"] = mood_word + " 🎨"
    return result


def _get_instructor_context() -> str:
    """강사 프로필을 문구 생성용 컨텍스트로 변환"""
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
        "신규 커리큘럼": '{"bannerSub":"10자이내","bannerTitle":"20자이내","bannerLead":"40-60자 수험생 심리 자극 문구","ctaCopy":"10자이내","ctaTitle":"CTA 제목","ctaSub":"30자이내","ctaBadge":"15자이내","statBadges":[],"introTitle":"20자이내","introDesc":"50-80자 강사 차별점","introBio":"강사 학습법 포함 40자이내","introBadges":[],"whyTitle":"20자이내","whySub":"30자이내","whyReasons":[["이모지","12자제목","45자구체설명"],["이모지","12자","45자"],["이모지","12자","45자"]],"curriculumTitle":"20자이내","curriculumSub":"30자이내","curriculumSteps":[["01","8자","각 단계 학생에게 필요한 이유 20자","기간"],["02","8자","20자","기간"],["03","8자","20자","기간"],["04","8자","20자","기간"]],"targetTitle":"20자이내","targetItems":["25자이내","항목2","항목3","항목4"],"reviews":[["30자이내 구체적 변화 인용문","이름","변화뱃지"],["인용문","이름","뱃지"],["인용문","이름","뱃지"]],"faqs":[["구체적 질문15자","답변40자"],["질문","답변"],["질문","답변"]]}',
        "이벤트": '{"bannerSub":"10자","bannerTitle":"20자","bannerLead":"50자 긴박감","ctaCopy":"10자","ctaTitle":"CTA","ctaSub":"30자","ctaBadge":"15자","statBadges":[],"eventTitle":"20자","eventDesc":"40자","eventDetails":[["📅","이벤트 기간","날짜"],["🎯","대상","값"],["💰","혜택","값"]],"benefitsTitle":"20자","eventBenefits":[{"icon":"이모지","title":"혜택명","desc":"35자","badge":"8자","no":"01"},{"icon":"이모지","title":"혜택명","desc":"35자","badge":"8자","no":"02"},{"icon":"이모지","title":"혜택명","desc":"35자","badge":"8자","no":"03"}],"deadlineTitle":"20자","deadlineMsg":"60자 긴박감","reviews":[["30자 인용문","이름","뱃지"],["인용문","이름","뱃지"],["인용문","이름","뱃지"]]}',
        "기획전": '{"festHeroTitle":"20자","festHeroCopy":"30자","festHeroSub":"40자","festHeroStats":[["수치","라벨"],["수치","라벨"],["수치","라벨"],["수치","라벨"]],"festLineupTitle":"20자","festLineupSub":"40자","festLineup":[{"name":"강사명","tag":"분야8자","tagline":"30자","badge":"8자","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"소개","badge":"뱃지","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"소개","badge":"뱃지","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"소개","badge":"뱃지","emoji":"이모지"}],"festBenefitsTitle":"20자","festBenefits":[{"icon":"이모지","title":"혜택명","desc":"35자","badge":"8자","no":"01"},{"icon":"이모지","title":"혜택명","desc":"35자","badge":"8자","no":"02"},{"icon":"이모지","title":"혜택명","desc":"35자","badge":"8자","no":"03"},{"icon":"이모지","title":"혜택명","desc":"35자","badge":"8자","no":"04"}],"festCtaTitle":"CTA제목","festCtaSub":"40자"}',
    }
    prompt = f"""당신은 대한민국 수능 교육 랜딩페이지 카피라이터입니다.

===강사 정보===
{inst_ctx}

===페이지 정보===
맥락: "{ctx}"
목적: {ptype} | 대상: {tgt} | 브랜드: {plabel}

===필수 규칙===
1. 강사 고유 학습법/슬로건/스타일이 있으면 반드시 문구에 녹여넣기 (매우 중요)
2. 수험생의 구체적 고민을 해결하는 문구 (예: "빈칸 하나가 등급을 가른다", "3주 후 독해 속도가 달라진다")
3. 확인되지 않은 수치(만족도%, 합격생수, 경력년수) 절대 금지 — statBadges, introBadges는 반드시 빈 배열 []
4. 한자(漢字) 절대 금지 — 한글/영문만 사용
5. curriculumSteps 설명: 각 단계가 왜 필요한지 학생 입장에서 설득

JSON만 반환 (마크다운 없이, 줄바꿈 없이):
{schemas.get(ptype, schemas['신규 커리큘럼'])}"""
    return safe_json(call_ai(prompt, max_tokens=2500))


def gen_section(sec_id: str) -> dict:
    inst_ctx = _get_instructor_context()
    schemas = {
        "banner": '{"bannerSub":"10자","bannerTitle":"20자","bannerLead":"50자 수험생 심리 자극","ctaCopy":"10자","statBadges":[]}',
        "intro":  '{"introTitle":"20자","introDesc":"60자 강사 차별점","introBio":"40자","introBadges":[]}',
        "why":    '{"whyTitle":"20자","whySub":"30자","whyReasons":[["이모지","12자","45자구체설명"],["이모지","12자","45자"],["이모지","12자","45자"]]}',
        "curriculum": '{"curriculumTitle":"20자","curriculumSub":"30자","curriculumSteps":[["01","8자","20자이유","기간"],["02","8자","20자","기간"],["03","8자","20자","기간"],["04","8자","20자","기간"]]}',
        "target": '{"targetTitle":"20자","targetItems":["25자","항목2","항목3","항목4"]}',
        "reviews": '{"reviews":[["30자구체변화인용문","이름","뱃지"],["인용문","이름","뱃지"],["인용문","이름","뱃지"]]}',
        "faq":    '{"faqs":[["15자질문","40자답변"],["질문","답변"],["질문","답변"]]}',
        "cta":    '{"ctaTitle":"CTA제목","ctaSub":"30자","ctaCopy":"10자","ctaBadge":"15자"}',
    }
    sec_name = SEC_LABELS.get(sec_id, sec_id)
    schema = schemas.get(sec_id, '{"title":"제목","desc":"설명"}')
    prompt = f"""수능 교육 카피라이터. "{sec_name}" 섹션만 새롭게 생성.

{inst_ctx}
과목: {st.session_state.subject} | 브랜드: {st.session_state.purpose_label}

규칙: 강사 고유 특성 반영, 구체적 문구, 한자 금지, 수치 금지([] 사용)
JSON만 반환: {schema}"""
    return safe_json(call_ai(prompt, max_tokens=600))


def gen_custom_sec(topic: str) -> dict:
    inst_ctx = _get_instructor_context()
    prompt = f"""수능 교육 랜딩페이지 카피라이터. "{topic}" 주제 섹션 생성.
{inst_ctx} | 과목: {st.session_state.subject}
한자 금지. JSON만 반환:
{{"tag":"8자이내","title":"20자이내","desc":"60자이내","items":[{{"icon":"이모지","title":"15자","desc":"45자"}},{{"icon":"이모지","title":"15자","desc":"45자"}},{{"icon":"이모지","title":"15자","desc":"45자"}}]}}"""
    return safe_json(call_ai(prompt, max_tokens=600))


# ── 엑셀 기반 강사 DB (정확한 정보) ──
INSTRUCTOR_DB = {
    "이명학": {"found":True,"subject":"영어","platform":"대성마이맥",
        "bio":"대성마이맥 영어 강사. Syntax·R'gorithm·Read N' Logic 시리즈 운영.",
        "slogan":"영어, 논리로 끝낸다",
        "signatureMethods":["R'gorithm (독해 알고리즘)","Syntax (구문 분석)"],
        "signatureCurriculum":"Read N' Logic (빈칸·순서·삽입)",
        "teachingStyle":"구문 분석과 독해 논리를 체계적으로 연결",
        "desc":"R'gorithm으로 영어 지문 구조를 논리적으로 파악하게 만드는 강사"},
    "션티": {"found":True,"subject":"영어","platform":"대성마이맥",
        "bio":"대성마이맥 영어 강사. KISS 시리즈(KISSAVE·KISSCHEMA·KISS Logic)로 수능 영어 완성.",
        "slogan":"KISS — Keep It Simple, Suneung",
        "signatureMethods":["KISS Logic (독해·빈칸·순삽)","KISSAVE (입문)","KISSCHEMA (유형별)"],
        "signatureCurriculum":"주간 KISS FULL — 실전 반복 훈련",
        "teachingStyle":"수능 영어 핵심 원리를 KISS 방법론으로 단순화하여 반복 훈련",
        "desc":"KISS 시리즈로 처음부터 끝까지 체계적으로 수능 영어를 완성하는 강사"},
    "이미지": {"found":True,"subject":"수학","platform":"대성마이맥",
        "bio":"대성마이맥 수학 강사. 세젤쉬·미친개념·미친기분 시리즈 운영.",
        "slogan":"수학, 미치도록 쉽게",
        "signatureMethods":["세젤쉬 (세상에서 제일 쉬운)","미친개념","미친기분 (기출 분석)"],
        "signatureCurriculum":"미친기분 — 기출 완전 정복",
        "teachingStyle":"복잡한 수학 개념을 직관적으로 쉽게 설명",
        "desc":"세젤쉬·미친개념으로 수학이 어려운 학생도 쉽게 따라올 수 있게 만드는 강사"},
    "김범준": {"found":True,"subject":"수학","platform":"대성마이맥",
        "bio":"대성마이맥 수학 강사. Starting Block·KICE Anatomy·The Hurdling 시리즈 운영.",
        "slogan":"수능 수학의 뼈대를 세워라",
        "signatureMethods":["KICE Anatomy (기출 해부)","Starting Block (개념 기초)","The Hurdling (문제풀이)"],
        "signatureCurriculum":"KICE Anatomy — 수능 수학 기출 해부",
        "teachingStyle":"수능 기출을 철저히 해부하여 출제 원리를 파악",
        "desc":"KICE Anatomy로 수능 수학 기출의 원리를 완전히 이해시키는 강사"},
    "김승리": {"found":True,"subject":"국어","platform":"대성마이맥",
        "bio":"대성마이맥 국어 강사. All Of KICE·VIC-FLIX(EBS 연계) 시리즈 운영.",
        "slogan":"국어, 승리로 끝낸다",
        "signatureMethods":["All Of KICE (수능 국어 전 범위)","VIC-FLIX (EBS 연계)"],
        "signatureCurriculum":"All Of KICE predator — 독서·문학 완성",
        "teachingStyle":"수능 국어 출제 원리 파악 후 실전 풀이 능력 강화",
        "desc":"All Of KICE 시리즈로 수능 국어를 원리부터 실전까지 완성하는 강사"},
    "유대종": {"found":True,"subject":"국어","platform":"대성마이맥",
        "bio":"대성마이맥 국어 강사. 인셉션 시리즈·파노라마 문학/독서·O.V.S(EBS 연계) 운영.",
        "slogan":"국어의 인셉션을 시작하라",
        "signatureMethods":["인셉션 (독해·문학·독서)","O.V.S (EBS 연계)","파노라마 (문학·독서 문제풀이)"],
        "signatureCurriculum":"인셉션 독서·문학 — 국어 개념 완성",
        "teachingStyle":"국어 독해와 문학을 인셉션 방식으로 깊이 이해시키는 체계적 강의",
        "desc":"인셉션 시리즈로 국어의 깊은 원리를 차근차근 이해시키는 강사"},
    "임정환": {"found":True,"subject":"사회","platform":"대성마이맥",
        "bio":"대성마이맥 사회탐구 강사. LIM IT·IMFACT·ALL LIM'S PICK 시리즈로 사문·생윤·윤사 전문.",
        "slogan":"사탐은 LIM이 끝낸다",
        "signatureMethods":["LIM IT (개념 완성)","IMFACT (심화)","ALL LIM'S PICK (문제풀이)"],
        "signatureCurriculum":"LIM IT → IMFACT → ALL LIM'S PICK 3단계",
        "teachingStyle":"사회탐구 개념을 LIM 3단계로 체계적으로 완성",
        "desc":"사회문화·생활과윤리·윤리와사상을 LIM 시리즈로 완전 정복하는 강사"},
    "최여름": {"found":True,"subject":"사회","platform":"대성마이맥",
        "bio":"대성마이맥 사회탐구 강사. BLZA SUMMER 시리즈로 사회문화 전 범위 완성.",
        "slogan":"여름처럼 뜨겁게, 사탐을 정복하라",
        "signatureMethods":["BLZA SUMMER (개념·기출·심화 통합)","SUMMER N제"],
        "signatureCurriculum":"BLZA SUMMER 1~5 — 사회문화 완전 정복",
        "teachingStyle":"BLZA SUMMER 시리즈로 개념부터 모의고사까지 단계별 완성",
        "desc":"BLZA SUMMER 시리즈로 사회문화를 처음부터 끝까지 완성하는 강사"},
    "방인혁": {"found":True,"subject":"과학","platform":"대성마이맥",
        "bio":"대성마이맥 물리학 강사. The Fundamentals·BIG BANG 모의고사 시리즈 운영.",
        "slogan":"물리학, 본질을 꿰뚫어라",
        "signatureMethods":["The Fundamentals (개념완성)","Problem Solving (기출)","BIG BANG 모의고사"],
        "signatureCurriculum":"The Fundamentals — 물리학 개념 완성",
        "teachingStyle":"물리학 본질적 원리부터 체계적으로 접근",
        "desc":"물리학 개념의 본질을 The Fundamentals로 완전히 이해시키는 강사"},
    "배기범": {"found":True,"subject":"과학","platform":"메가스터디",
        "bio":"메가스터디 물리학 강사. PLAN B 시리즈·기범비급·3순환 기출특강으로 물리학 완성.",
        "slogan":"물리학은 PLAN B가 있다",
        "signatureMethods":["PLAN B (문제풀이 Tool)","기범비급 (심화)","3순환 기출특강"],
        "signatureCurriculum":"PLAN B — 물리학 문제풀이 Tool 완전 정복",
        "teachingStyle":"물리학 문제풀이 핵심 도구를 PLAN B로 체계적 훈련",
        "desc":"PLAN B 시리즈로 물리학 문제풀이 핵심 기술을 완전히 습득시키는 강사"},
}

def search_instructor(name: str, subj: str) -> dict:
    """엑셀 DB 우선 검색, 없으면 AI 보조 (환각 방지)"""
    # 이름 정확 매칭 먼저
    if name in INSTRUCTOR_DB:
        return INSTRUCTOR_DB[name]
    # 부분 매칭 시도
    for db_name, info in INSTRUCTOR_DB.items():
        if name in db_name or db_name in name:
            return info
    # DB에 없는 강사 — AI에게 묻되 매우 보수적으로
    prompt = f"""한국 수능 강사 "{name}" ({subj} 과목). 
정말 확실히 아는 정보만 답하세요. 모르면 반드시 빈 문자열.
절대 지어내지 마세요. 한자 금지.
JSON만: {{"found":true,"bio":"1문장","slogan":"","signatureMethods":[],"teachingStyle":"1문장","desc":"1문장"}}"""
    try:
        return safe_json(call_ai(prompt, max_tokens=300))
    except Exception:
        return {"found": True, "bio": f"{subj} 강사", "slogan": "",
                "signatureMethods": [], "teachingStyle": "", "desc": ""}

# ══════════════════════════════════════
# 테마 리졸버
# ══════════════════════════════════════
def get_theme() -> dict:
    if st.session_state.concept == "custom" and st.session_state.custom_theme:
        ct = st.session_state.custom_theme
        df  = ct.get("displayFont","Noto Sans KR")
        bf  = ct.get("bodyFont","Noto Sans KR")
        fw  = ct.get("fontWeights","400;700;900")
        dfw = ct.get("displayFontWeights","400;700")
        r   = ct.get("borderRadiusPx",8)
        rb  = ct.get("btnBorderRadiusPx",100)
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
                "dark":ct.get("dark",True),"heroStyle":ct.get("heroStyle","split"),
                "cta":ct.get("ctaGradient",f"linear-gradient(135deg,{ct['c4']},{ct['c1']})")}
    t = THEMES.get(st.session_state.concept, THEMES["sakura"])
    return {"fonts":t["fonts"],"vars":t["vars"],"extra_css":t.get("extra_css",""),
            "dark":t.get("dark",False),"heroStyle":t.get("heroStyle","split"),
            "cta":t.get("cta","linear-gradient(135deg,var(--c4),var(--c1))")}

# ══════════════════════════════════════
# BASE CSS
# ══════════════════════════════════════
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

# ══════════════════════════════════════
# 섹션 빌더
# ══════════════════════════════════════
def _bg(bg_url, dark):
    if not bg_url:
        return {"hero_bg":f"background:var(--bg)","overlay":"",
                "tc":"color:var(--text)","t70c":"color:var(--t70)",
                "c1c":"var(--c1)","bdc":"var(--bd)",
                "card_bg":"rgba(255,255,255,.05)" if dark else "var(--bg)",
                "btn_s":"","top_brd":"var(--bd)","blur":""}
    return {"hero_bg":f"background:var(--bg) url('{bg_url}') center/cover no-repeat",
            "overlay":'<div style="position:absolute;inset:0;background:rgba(0,0,0,0.58);z-index:1;pointer-events:none"></div>',
            "tc":"color:#fff","t70c":"color:rgba(255,255,255,.82)",
            "c1c":"#fff","bdc":"rgba(255,255,255,.25)",
            "card_bg":"rgba(0,0,0,.65)",
            "btn_s":"color:#fff;border-color:rgba(255,255,255,.5)",
            "top_brd":"rgba(255,255,255,.2)","blur":"backdrop-filter:blur(12px);"}

def sec_banner(d, cp, T):
    sub    = strip_hanja(cp.get("bannerSub", d["subject"]+" 완성"))
    title  = strip_hanja(cp.get("bannerTitle", d["purpose_label"]))
    lead   = strip_hanja(cp.get("bannerLead", f"{d['target']}을 위한 커리큘럼"))
    cta    = strip_hanja(cp.get("ctaCopy", "수강신청하기"))
    stats  = cp.get("statBadges", [])
    kws    = SUBJ_KW.get(d["subject"], ["개념","기출","실전","파이널"])
    bg_url = cp.get("bg_photo_url", "")
    hs     = T.get("heroStyle", "split")
    s      = _bg(bg_url, T["dark"])

    kh = "".join(f'<span style="font-size:9.5px;font-weight:700;padding:5px 12px;border-radius:var(--r-btn,100px);color:{s["c1c"]};border:1px solid {s["bdc"]};margin:2px">{k}</span>' for k in kws)
    sh = "".join(f'<div><div style="font-family:var(--fh);font-size:clamp(18px,2.8vw,26px);font-weight:900;color:{s["c1c"]}">{sv}</div><div style="font-size:9px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;{s["t70c"]};margin-top:2px">{sl}</div></div>' for sv,sl in stats) if stats else ""
    inst = f'<div style="display:inline-flex;align-items:center;gap:8px;margin-top:18px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:4px;padding:5px 14px"><span style="font-size:11px;{s["t70c"]}">{d["name"]} 선생님</span></div>' if d["name"] else ""

    if hs == "immersive":
        return (
            f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:flex;flex-direction:column;justify-content:flex-end">'
            + s["overlay"] +
            '<div style="position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.88) 0%,rgba(0,0,0,.15) 65%,transparent 100%);z-index:1;pointer-events:none"></div>'
            f'<div style="position:relative;z-index:2;padding:clamp(48px,7vw,80px) clamp(32px,6vw,88px);max-width:860px">'
            f'<div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.12);{s["blur"]}padding:5px 16px;border-radius:100px;margin-bottom:20px;border:1px solid rgba(255,255,255,.2);font-size:10px;font-weight:700;color:#fff;letter-spacing:.14em;text-transform:uppercase">{sub}</div>'
            f'<h1 style="font-family:var(--fh);font-size:clamp(52px,8vw,110px);font-weight:900;line-height:.85;letter-spacing:-.05em;color:#fff;margin-bottom:18px" class="st">{title}</h1>'
            f'<p style="font-size:clamp(14px,1.6vw,17px);line-height:1.85;color:rgba(255,255,255,.78);max-width:520px;margin-bottom:24px">{lead}</p>'
            f'<div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:24px">{kh}</div>'
            + inst +
            f'<div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:22px">'
            f'<a class="btn-p" href="#" style="box-shadow:0 0 28px rgba(255,255,255,.12)">{cta} →</a>'
            f'<a href="#" style="display:inline-flex;align-items:center;gap:7px;background:rgba(255,255,255,.1);{s["blur"]}color:#fff;font-weight:600;padding:13px 28px;border-radius:100px;border:1.5px solid rgba(255,255,255,.3);font-size:14px;text-decoration:none">강의 미리보기</a></div>'
            + (f'<div style="display:flex;gap:36px;margin-top:40px;padding-top:24px;border-top:1px solid rgba(255,255,255,.2)">{sh}</div>' if sh else "")
            + '</div></section>'
        )
    else:  # split or editorial
        ci = "".join(f'<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid {s["bdc"]}"><span style="font-size:11px;font-weight:600;{s["t70c"]}">{l}</span><span style="font-size:11.5px;font-weight:700;{s["tc"]}">{v}</span></div>' for l,v in [["강의 대상",d["target"]],["과목",d["subject"]],["목적",d["purpose_label"][:14]+"…"]])
        return (
            f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:grid;grid-template-columns:1fr 360px">'
            + s["overlay"] +
            f'<div style="position:relative;z-index:2;display:flex;flex-direction:column;justify-content:center;padding:clamp(60px,8vw,100px) clamp(24px,4vw,52px) clamp(60px,8vw,100px) clamp(32px,6vw,88px)">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:28px"><div style="width:32px;height:2px;background:{s["c1c"]}"></div><span style="font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;{s["tc"]}">{sub}</span></div>'
            f'<h1 style="font-family:var(--fh);font-size:clamp(40px,6vw,84px);font-weight:900;line-height:.88;letter-spacing:-.05em;{s["tc"]}" class="st">{title}</h1>'
            f'<p style="font-size:clamp(13px,1.4vw,15.5px);line-height:2;{s["t70c"]};margin-top:20px;max-width:420px;padding-left:14px;border-left:2px solid {s["c1c"]}">{lead}</p>'
            f'<div style="display:flex;gap:5px;flex-wrap:wrap;margin-top:18px">{kh}</div>'
            + inst +
            f'<div style="display:flex;gap:12px;margin-top:26px"><a class="btn-p" href="#">{cta} →</a><a class="btn-s" href="#" style="{s["btn_s"]}">강의 미리보기</a></div>'
            + (f'<div style="display:flex;gap:28px;margin-top:48px;padding-top:24px;border-top:1px solid {s["top_brd"]}">{sh}</div>' if sh else "")
            + f'</div>'
            f'<div style="background:rgba(0,0,0,.18);border-left:1px solid {s["bdc"]};display:flex;align-items:center;justify-content:center;padding:48px 24px;position:relative;z-index:2">'
            f'<div style="width:100%;background:{s["card_bg"]};border:1px solid {s["bdc"]};border-radius:var(--r,12px);overflow:hidden;{s["blur"]}">'
            f'<div style="background:var(--c1);padding:18px 22px;text-align:center"><div style="font-family:var(--fh);font-size:19px;font-weight:900;color:#fff;line-height:1.25">{title}</div></div>'
            f'<div style="padding:18px 22px">{ci}<a class="btn-p" href="#" style="width:100%;justify-content:center;margin-top:14px;display:flex">{cta} →</a></div>'
            f'</div></div></section>'
        )

def sec_intro(d, cp, T):
    ip   = st.session_state.get("inst_profile") or {}
    t    = strip_hanja(cp.get("introTitle", f"{d['name']} 선생님 소개" if d["name"] else f"{d['subject']} 강사 소개"))
    desc = strip_hanja(cp.get("introDesc", f"{d['subject']} 최상위권 합격의 비결"))
    bio  = strip_hanja(cp.get("introBio", ip.get("desc", f"검증된 {d['subject']} 강사")))
    badges = cp.get("introBadges", [])
    methods = [strip_hanja(m) for m in (ip.get("signatureMethods") or []) if m and m not in ("없음","")]
    slogan  = strip_hanja(ip.get("slogan",""))
    bh = "".join(f'<div style="text-align:center;padding:16px;border:1px solid var(--bd);border-radius:var(--r,10px)"><div style="font-family:var(--fh);font-size:22px;font-weight:900;color:var(--c1)">{bv}</div><div style="font-size:9px;color:var(--t45);font-weight:600;letter-spacing:.1em;text-transform:uppercase;margin-top:3px">{bl}</div></div>' for bv,bl in badges) if badges else ""
    mtags = "".join(f'<span style="background:var(--c1);color:#fff;font-size:10px;font-weight:700;padding:4px 14px;border-radius:100px;margin:3px 4px 3px 0;display:inline-flex">{m}</span>' for m in methods[:3]) if methods else ""
    sq = f'<div style="margin-top:14px;padding:14px 18px;background:var(--bg3);border-radius:var(--r,8px);border-left:3px solid var(--c1)"><span style="font-size:13px;color:var(--text);font-style:italic">"{slogan}"</span></div>' if slogan else ""
    bsec = f'<div style="display:grid;grid-template-columns:repeat({min(len(badges),4)},1fr);gap:10px;margin-bottom:14px" class="rv d1">{bh}</div>' if bh else ""
    return (f'<section class="sec alt" id="intro"><div class="rv"><div class="tag-line">강사 소개</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{desc}</p></div>'
            + bsec
            + (f'<div style="display:flex;flex-wrap:wrap;margin-bottom:12px">{mtags}</div>' if mtags else "")
            + f'<div style="padding:16px 20px;border-left:3px solid var(--c1);background:var(--bg3);border-radius:0 var(--r,8px) var(--r,8px) 0" class="rv d2"><p style="font-size:13px;line-height:1.9;color:var(--t70)">{bio}</p></div>'
            + sq + '</section>')

def sec_why(d, cp, T):
    t = strip_hanja(cp.get("whyTitle","이 강의가 필요한 이유"))
    s = strip_hanja(cp.get("whySub", f"{d['subject']} 1등급의 비결"))
    reasons = cp.get("whyReasons",[["🎯","유형별 완전 정복","수능 출제 유형을 완전히 분석하여 어떤 문제도 흔들리지 않는 실력을 만듭니다."],["📊","기출 데이터 분석","최근 5년 기출을 철저히 분석하여 실전에서 반드시 나오는 유형만 집중 훈련합니다."],["⚡","실전 속도 훈련","정확도와 속도를 동시에 잡아 70분 안에 45문항을 완벽히 소화하는 훈련을 합니다."]])
    safe_reasons = []
    for item in reasons:
        if isinstance(item, (list, tuple)) and len(item) >= 3:
            safe_reasons.append((str(item[0]), str(item[1]), str(item[2])))
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            safe_reasons.append(("✦", str(item[0]), str(item[1])))
        elif isinstance(item, dict):
            safe_reasons.append((item.get("icon","✦"), item.get("title",""), item.get("desc","")))
    rh = "".join(f'<div class="card"><div style="display:flex;align-items:center;gap:12px;margin-bottom:14px"><div style="width:44px;height:44px;border-radius:var(--r,12px);background:var(--c1);display:flex;align-items:center;justify-content:center;font-size:20px">{ic}</div><div style="font-family:var(--fh);font-size:15px;font-weight:700" class="st">{strip_hanja(tt)}</div></div><p style="font-size:13px;line-height:1.85;color:var(--t70)">{strip_hanja(dc)}</p></div>' for ic,tt,dc in safe_reasons)
    return f'<section class="sec" id="why"><div class="rv"><div class="tag-line">수강 이유</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{s}</p></div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px" class="rv d1">{rh}</div></section>'

def sec_curriculum(d, cp, T):
    t = strip_hanja(cp.get("curriculumTitle",f"{d['purpose_label']} 커리큘럼"))
    s = strip_hanja(cp.get("curriculumSub","체계적인 4단계 완성 로드맵"))
    steps = cp.get("curriculumSteps",[["01","개념 완성","핵심 개념과 공식, 왜 이 단계가 필요한지 이해합니다.","4주"],["02","유형 훈련","기출을 완전히 분석하여 출제 패턴을 파악합니다.","4주"],["03","심화 특훈","고난도 문항의 아이디어를 완전히 내 것으로 만듭니다.","4주"],["04","파이널","실수 제거와 시간 배분으로 실전을 완성합니다.","4주"]])
    sh = "".join(f'<div class="card" style="position:relative;overflow:hidden"><div style="position:absolute;top:-12px;right:-8px;font-family:var(--fh);font-size:80px;font-weight:900;color:var(--c1);opacity:.05;line-height:1">{no}</div><div style="font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--c1);margin-bottom:8px">STEP {no}</div><div style="font-family:var(--fh);font-size:16px;font-weight:700;margin-bottom:6px" class="st">{strip_hanja(tt)}</div><div style="font-size:12px;color:var(--t70);margin-bottom:8px;line-height:1.6">{strip_hanja(dc)}</div><span style="font-size:10px;background:var(--c1);color:#fff;padding:3px 10px;border-radius:100px;font-weight:700">{du}</span></div>' for no,tt,dc,du in steps)
    return f'<section class="sec alt" id="curriculum"><div class="rv"><div class="tag-line">커리큘럼</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{s}</p></div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px" class="rv d1">{sh}</div></section>'

def sec_target(d, cp, T):
    t = strip_hanja(cp.get("targetTitle","이런 분들께 추천합니다"))
    items = [strip_hanja(str(it)) for it in cp.get("targetItems",[
        f"수능까지 {d['subject']} 점수를 확실히 올리고 싶은 분",
        "개념은 아는데 실전에서 점수가 안 나오는 분",
        "N수를 준비하며 체계적인 커리큘럼이 필요한 분",
        f"{d['subject']} 상위권 도약을 원하는 분"])]
    ih = "".join(f'<div class="card" style="display:flex;align-items:center;gap:13px;padding:16px 20px"><div style="width:26px;height:26px;min-width:26px;border-radius:50%;background:var(--c1);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;color:#fff">{i+1}</div><span style="font-size:14px;font-weight:500;line-height:1.5">{txt}</span></div>' for i,txt in enumerate(items))
    return f'<section class="sec" id="target"><div class="rv"><div class="tag-line">수강 대상</div><h2 class="sec-h2 st">{t}</h2></div><div style="display:flex;flex-direction:column;gap:8px" class="rv d1">{ih}</div></section>'

def sec_reviews(d, cp, T):
    reviews = cp.get("reviews",[[f'"개념이 이렇게 명확하게 보인 적이 없었어요. {d["subject"]} 공부가 달라졌습니다."',"고3 김OO","등급 향상"],['"3주 만에 독해 속도가 확실히 빨라졌어요. 실전에서 시간이 남는 게 느껴졌습니다."',"N수 이OO","실전 완성"],[f'"선생님 덕분에 {d["subject"]} 구조가 보이기 시작했어요. 빈칸이 겁나지 않습니다."',"고2 박OO","자신감 회복"]])
    rh = "".join(f'<div class="card" style="display:flex;flex-direction:column;gap:10px"><div style="color:#F59E0B;font-size:11px">★★★★★</div><p style="font-size:13px;line-height:1.85;font-weight:500">{strip_hanja(txt)}</p><div style="display:flex;align-items:center;justify-content:space-between;padding-top:10px;border-top:1px solid var(--bd)"><span style="font-size:11px;color:var(--t45)">— {nm} 학생</span><span style="font-size:10px;background:var(--bg3);color:var(--c1);padding:3px 10px;border-radius:100px;font-weight:700;border:1px solid var(--bd)">{badge}</span></div></div>' for txt,nm,badge in reviews)
    return f'<section class="sec alt" id="reviews"><div class="rv"><div class="tag-line">수강평</div><h2 class="sec-h2 st">생생한 수강생 후기</h2></div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px" class="rv d1">{rh}</div></section>'

def sec_faq(d, cp, T):
    raw = cp.get("faqs",[["수강 기간은 얼마나 되나요?","기본 30일이며, 연장권으로 최대 90일 가능합니다."],["교재는 별도 구매인가요?","별도 구매이며, 신청 페이지에서 함께 구매하실 수 있습니다."],["모바일에서도 수강 가능한가요?","PC와 모바일 모두 가능합니다."]])
    faqs = []
    for item in raw:
        if isinstance(item, dict):   faqs.append([item.get("question",item.get("q","")), item.get("answer",item.get("a",""))])
        elif isinstance(item, list) and len(item)>=2: faqs.append([str(item[0]),str(item[1])])
    fh = "".join(f'<div style="border:1px solid var(--bd);border-radius:var(--r,10px);overflow:hidden;margin-bottom:6px"><div style="padding:13px 17px;background:var(--bg3);display:flex;gap:9px"><span style="color:var(--c1);font-weight:800;font-size:14px;flex-shrink:0">Q</span><span style="font-weight:600;font-size:13px">{strip_hanja(q)}</span></div><div style="padding:12px 17px;background:var(--bg);display:flex;gap:9px"><span style="color:var(--t45);font-weight:700;font-size:14px;flex-shrink:0">A</span><span style="font-size:13px;line-height:1.75;color:var(--t70)">{strip_hanja(a)}</span></div></div>' for q,a in faqs)
    return f'<section class="sec" id="faq"><div class="rv"><div class="tag-line">FAQ</div><h2 class="sec-h2 st">자주 묻는 질문</h2></div><div class="rv d1">{fh}</div></section>'

def sec_cta(d, cp, T):
    tt    = strip_hanja(cp.get("ctaTitle", f"지금 바로 시작해<br>{d['subject']} 1등급을 확보하세요"))
    sub   = strip_hanja(cp.get("ctaSub",  f"{d['name']} 선생님과 함께라면 가능합니다." if d["name"] else f"{d['subject']} 1등급, 지금 시작하세요."))
    cc    = strip_hanja(cp.get("ctaCopy", "지금 수강신청하기"))
    badge = strip_hanja(cp.get("ctaBadge", f"{d['target']} 전용"))
    return (f'<section style="padding:clamp(64px,9vw,100px) clamp(24px,6vw,72px);text-align:center;position:relative;overflow:hidden;background:{T["cta"]}">'
            f'<div style="position:absolute;top:-100px;right:-100px;width:400px;height:400px;border-radius:50%;background:rgba(255,255,255,.04);pointer-events:none"></div>'
            f'<div style="position:relative;z-index:1"><div style="display:inline-block;background:rgba(255,255,255,.10);padding:5px 16px;border-radius:100px;font-size:10px;font-weight:700;color:#fff;margin-bottom:18px">{badge}</div>'
            f'<h2 style="font-family:var(--fh);font-size:clamp(26px,4.5vw,48px);font-weight:900;line-height:1.15;letter-spacing:-.03em;color:#fff;margin-bottom:12px">{tt}</h2>'
            f'<p style="color:rgba(255,255,255,.65);font-size:15px;margin-bottom:36px">{sub}</p>'
            f'<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap"><a style="display:inline-flex;align-items:center;gap:7px;background:#fff;color:#0A0A0A;font-weight:800;padding:14px 40px;border-radius:100px;font-size:15px;text-decoration:none" href="#">{cc} →</a>'
            f'<a style="display:inline-flex;align-items:center;gap:7px;background:transparent;color:rgba(255,255,255,.8);font-weight:600;padding:13px 28px;border-radius:100px;border:1.5px solid rgba(255,255,255,.3);font-size:14px;text-decoration:none" href="#">카카오톡 문의</a></div></div></section>')

def sec_event_overview(d, cp, T):
    t = strip_hanja(cp.get("eventTitle", d["purpose_label"]))
    desc = strip_hanja(cp.get("eventDesc","이 이벤트는 기간 한정으로 진행됩니다."))
    details = cp.get("eventDetails",[["📅","이벤트 기간","2026년 4월 1일 — 4월 30일"],["🎯","대상","고3·N수"],["💰","혜택","최대 30% 할인"]])
    dh = "".join(f'<div class="card" style="text-align:center;padding:28px 20px"><div style="font-size:32px;margin-bottom:12px">{ic}</div><div style="font-size:11px;font-weight:700;color:var(--c1);letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px">{lb}</div><div style="font-family:var(--fh);font-size:18px;font-weight:700">{vl}</div></div>' for ic,lb,vl in details)
    return f'<section class="sec" id="event-overview"><div class="rv"><div class="tag-line">이벤트 개요</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{desc}</p></div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px" class="rv d1">{dh}</div></section>'

def sec_event_benefits(d, cp, T):
    t = strip_hanja(cp.get("benefitsTitle","이벤트 특별 혜택"))
    benefits = cp.get("eventBenefits",[{"icon":"🎁","title":"수강료 특가","desc":"이벤트 기간 최대 30% 할인.","badge":"최대 30%","no":"01"},{"icon":"📚","title":"교재 무료 제공","desc":"핵심 교재가 무료로 제공됩니다.","badge":"무료 제공","no":"02"},{"icon":"🔥","title":"라이브 특강","desc":"매주 토요일 라이브 특강 무료.","badge":"매주 토요일","no":"03"}])
    bh = "".join(f'<div class="card" style="display:grid;grid-template-columns:60px 1fr;gap:18px;align-items:flex-start;padding:22px"><div style="width:60px;height:60px;border-radius:var(--r,14px);background:linear-gradient(135deg,var(--c1),var(--c2));display:flex;align-items:center;justify-content:center;font-size:26px;flex-shrink:0">{b["icon"]}</div><div><div style="display:flex;align-items:center;gap:7px;margin-bottom:7px"><span style="font-size:9px;font-weight:800;color:var(--c1);opacity:.7">NO.{b["no"]}</span><span style="background:var(--c1);color:#fff;font-size:9px;font-weight:700;padding:2px 9px;border-radius:100px">{b["badge"]}</span></div><div style="font-family:var(--fh);font-size:15px;font-weight:700;margin-bottom:7px" class="st">{strip_hanja(b["title"])}</div><p style="font-size:12px;line-height:1.82;color:var(--t70)">{strip_hanja(b["desc"])}</p></div></div>' for b in benefits)
    return f'<section class="sec alt" id="event-benefits"><div class="rv"><div class="tag-line">이벤트 혜택</div><h2 class="sec-h2 st">{t}</h2></div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px" class="rv d1">{bh}</div></section>'

def sec_event_deadline(d, cp, T):
    t = strip_hanja(cp.get("deadlineTitle","마감 안내"))
    msg = strip_hanja(cp.get("deadlineMsg","이벤트는 기간 한정으로 운영됩니다."))
    cc = strip_hanja(cp.get("ctaCopy","이벤트 신청하기"))
    return (f'<section class="sec" id="event-deadline" style="background:{T["cta"]};text-align:center">'
            f'<div class="rv"><div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.15);padding:6px 20px;border-radius:100px;font-size:11px;font-weight:700;color:#fff;margin-bottom:24px">⏰ 마감 안내</div>'
            f'<h2 style="font-family:var(--fh);font-size:clamp(24px,3.5vw,40px);font-weight:900;color:#fff;margin-bottom:16px" class="st">{t}</h2>'
            f'<p style="color:rgba(255,255,255,.7);font-size:15px;line-height:1.8;margin-bottom:36px;max-width:480px;margin-left:auto;margin-right:auto">{msg}</p>'
            f'<a style="display:inline-flex;align-items:center;gap:7px;background:#fff;color:#0A0A0A;font-weight:800;padding:14px 48px;border-radius:100px;font-size:16px;text-decoration:none" href="#">{cc} →</a></div></section>')

def sec_fest_hero(d, cp, T):
    t = strip_hanja(cp.get("festHeroTitle",f"{d['subject']} 기획전"))
    cc = strip_hanja(cp.get("festHeroCopy","최고의 강사들이 한 자리에"))
    sub = strip_hanja(cp.get("festHeroSub",f"수능 {d['subject']} 전 강사 라인업."))
    stats = cp.get("festHeroStats",[])
    sh = "".join(f'<div style="text-align:center"><div style="font-family:var(--fh);font-size:clamp(20px,3vw,32px);font-weight:900;color:var(--c1)">{sv}</div><div style="font-size:9px;color:rgba(255,255,255,.5);font-weight:600;letter-spacing:.1em;text-transform:uppercase;margin-top:3px">{sl}</div></div>' for sv,sl in stats) if stats else ""
    return (f'<section id="fest-hero" style="position:relative;min-height:80vh;overflow:hidden;background:{T["cta"]};display:flex;flex-direction:column;justify-content:center;text-align:center;padding:clamp(80px,10vw,120px) clamp(28px,6vw,80px)">'
            f'<div style="position:absolute;inset:0;background:radial-gradient(ellipse 80% 70% at 50% 30%,rgba(255,255,255,.08),transparent 65%);pointer-events:none"></div>'
            f'<div style="position:relative;z-index:2"><div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.12);backdrop-filter:blur(8px);padding:6px 20px;border-radius:100px;font-size:11px;font-weight:700;color:#fff;margin-bottom:24px;border:1px solid rgba(255,255,255,.2)">🏆 {d["subject"]} 기획전</div>'
            f'<h1 style="font-family:var(--fh);font-size:clamp(40px,7vw,100px);font-weight:900;line-height:.85;letter-spacing:-.05em;color:#fff;margin-bottom:20px" class="st">{t}</h1>'
            f'<p style="font-size:clamp(18px,2.5vw,24px);color:rgba(255,255,255,.75);margin-bottom:12px;font-weight:700">{cc}</p>'
            f'<p style="font-size:15px;color:rgba(255,255,255,.55);margin-bottom:48px;max-width:500px;margin-left:auto;margin-right:auto">{sub}</p>'
            + (f'<div style="display:flex;gap:48px;justify-content:center;flex-wrap:wrap;padding-top:40px;border-top:1px solid rgba(255,255,255,.15)">{sh}</div>' if sh else "")
            + '</div></section>')

def sec_fest_lineup(d, cp, T):
    t = strip_hanja(cp.get("festLineupTitle","강사 라인업"))
    s = strip_hanja(cp.get("festLineupSub",f"{d['subject']} 전 영역 최강 강사진"))
    lineup = cp.get("festLineup",[{"name":"강사A","tag":"독해·문법","tagline":"수능 영어 독해의 정석","badge":"베스트셀러","emoji":"📖"},{"name":"강사B","tag":"EBS 연계","tagline":"EBS 연계율 완벽 적중","badge":"적중률 1위","emoji":"🎯"},{"name":"강사C","tag":"어법·어휘","tagline":"어법·어휘 전문 빠른 풀이","badge":"속도UP","emoji":"⚡"},{"name":"강사D","tag":"파이널","tagline":"수능 D-30 파이널 완성","badge":"파이널 특화","emoji":"🏆"}])
    lh = "".join(f'<div class="card" style="text-align:center;padding:28px 20px"><div style="font-size:40px;margin-bottom:14px">{l["emoji"]}</div><div style="display:inline-flex;align-items:center;gap:6px;background:var(--bg3);color:var(--c1);font-size:9px;font-weight:700;padding:4px 12px;border-radius:100px;margin-bottom:12px;border:1px solid var(--bd)">{strip_hanja(l["tag"])}</div><div style="font-family:var(--fh);font-size:18px;font-weight:900;margin-bottom:8px" class="st">{strip_hanja(l["name"])}</div><p style="font-size:12px;line-height:1.7;color:var(--t70);margin-bottom:12px">{strip_hanja(l["tagline"])}</p><span style="font-size:10px;background:var(--c1);color:#fff;padding:4px 14px;border-radius:100px;font-weight:700">{strip_hanja(l["badge"])}</span></div>' for l in lineup)
    return f'<section class="sec alt" id="fest-lineup"><div class="rv"><div class="tag-line">강사 라인업</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{s}</p></div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px" class="rv d1">{lh}</div></section>'

def sec_fest_benefits(d, cp, T):
    t = strip_hanja(cp.get("festBenefitsTitle","기획전 특별 혜택"))
    benefits = cp.get("festBenefits",[{"icon":"🎁","title":"전 강사 통합 수강료 특가","desc":"최대 30% 추가 할인.","badge":"최대 30%","no":"01"},{"icon":"📚","title":"통합 학습 자료 무료","desc":"통합 교재 및 기출 자료 무료.","badge":"무료 제공","no":"02"},{"icon":"🔥","title":"주간 라이브 특강","desc":"매주 전 강사 참여 라이브.","badge":"전 강사 참여","no":"03"},{"icon":"🏆","title":"목표 등급 보장","desc":"목표 등급 미달성 시 재수강.","badge":"성적 보장","no":"04"}])
    bh = "".join(f'<div class="card" style="display:grid;grid-template-columns:60px 1fr;gap:18px;align-items:flex-start;padding:22px"><div style="width:60px;height:60px;border-radius:var(--r,14px);background:linear-gradient(135deg,var(--c1),var(--c2));display:flex;align-items:center;justify-content:center;font-size:26px;flex-shrink:0">{b["icon"]}</div><div><div style="display:flex;align-items:center;gap:7px;margin-bottom:7px"><span style="font-size:9px;font-weight:800;color:var(--c1);opacity:.7">NO.{b["no"]}</span><span style="background:var(--c1);color:#fff;font-size:9px;font-weight:700;padding:2px 9px;border-radius:100px">{b["badge"]}</span></div><div style="font-family:var(--fh);font-size:15px;font-weight:700;margin-bottom:7px" class="st">{strip_hanja(b["title"])}</div><p style="font-size:12px;line-height:1.82;color:var(--t70)">{strip_hanja(b["desc"])}</p></div></div>' for b in benefits)
    return f'<section class="sec" id="fest-benefits"><div class="rv"><div class="tag-line">기획전 혜택</div><h2 class="sec-h2 st">{t}</h2></div><div style="display:grid;grid-template-columns:repeat(2,1fr);gap:16px" class="rv d1">{bh}</div></section>'

def sec_fest_cta(d, cp, T):
    t = strip_hanja(cp.get("festCtaTitle",f"지금 바로 {d['subject']} 기획전<br>전체 강사 라인업을 만나세요"))
    s = strip_hanja(cp.get("festCtaSub",f"최고의 강사들과 함께 {d['subject']} 1등급 완성."))
    return (f'<section style="padding:clamp(64px,9vw,104px) clamp(24px,6vw,72px);text-align:center;position:relative;overflow:hidden;background:{T["cta"]}">'
            f'<div style="position:absolute;top:-120px;left:50%;transform:translateX(-50%);width:700px;height:700px;border-radius:50%;background:rgba(255,255,255,.03);pointer-events:none"></div>'
            f'<div style="position:relative;z-index:1"><div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.12);backdrop-filter:blur(8px);padding:6px 20px;border-radius:100px;font-size:11px;font-weight:700;color:#fff;margin-bottom:24px;border:1px solid rgba(255,255,255,.2)">🏆 {d["subject"]} 기획전 통합 신청</div>'
            f'<h2 style="font-family:var(--fh);font-size:clamp(28px,4.8vw,56px);font-weight:900;line-height:1.08;letter-spacing:-.03em;color:#fff;margin-bottom:16px">{t}</h2>'
            f'<p style="color:rgba(255,255,255,.62);font-size:15px;line-height:1.75;margin-bottom:42px;max-width:480px;margin-left:auto;margin-right:auto">{s}</p>'
            f'<div style="display:flex;gap:13px;justify-content:center;flex-wrap:wrap">'
            f'<a style="display:inline-flex;align-items:center;gap:8px;background:#fff;color:#0A0A0A;font-weight:800;padding:17px 48px;border-radius:100px;font-size:16px;text-decoration:none" href="#">기획전 통합 신청 →</a>'
            f'<a style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.1);backdrop-filter:blur(8px);color:rgba(255,255,255,.82);font-weight:600;padding:16px 30px;border-radius:100px;border:1.5px solid rgba(255,255,255,.3);font-size:14px;text-decoration:none" href="#">강사 개별 신청</a>'
            f'</div></div></section>')

def sec_custom(d, cp, T):
    c = cp.get("custom_section_data", {})
    if not c: return ""
    tag   = strip_hanja(c.get("tag","추가 안내"))
    title = strip_hanja(c.get("title","추가 섹션"))
    items = c.get("items",[])
    desc  = strip_hanja(c.get("desc",""))
    if items:
        ih = "".join(f'<div class="card"><div style="display:flex;align-items:center;gap:10px;margin-bottom:10px"><div style="width:36px;height:36px;min-width:36px;border-radius:50%;background:var(--c1);display:flex;align-items:center;justify-content:center;font-size:16px">{it.get("icon","✦")}</div><div style="font-family:var(--fh);font-size:14px;font-weight:700" class="st">{strip_hanja(it.get("title",""))}</div></div><p style="font-size:12.5px;line-height:1.85;color:var(--t70)">{strip_hanja(it.get("desc",""))}</p></div>' for it in items)
        cols = "repeat(3,1fr)" if len(items)>=3 else ("repeat(2,1fr)" if len(items)==2 else "1fr")
        body = f'<div style="display:grid;grid-template-columns:{cols};gap:12px" class="rv d1">{ih}</div>'
    else:
        body = f'<div class="rv d1"><p style="font-size:14px;line-height:1.9;color:var(--t70)">{desc}</p></div>'
    return f'<section class="sec" id="custom-section"><div class="rv"><div class="tag-line">{tag}</div><h2 class="sec-h2 st">{title}</h2></div>{body}</section>'

# ══════════════════════════════════════
# HTML 빌더
# ══════════════════════════════════════
def build_html(secs: list) -> str:
    T  = get_theme()
    cp = dict(st.session_state.custom_copy or {})
    if st.session_state.bg_photo_url:
        cp["bg_photo_url"] = st.session_state.bg_photo_url
    d  = {"name": st.session_state.instructor_name or "",
          "subject": st.session_state.subject,
          "purpose_label": st.session_state.purpose_label,
          "target": st.session_state.target}
    dc = ".card{background:var(--bg2)!important}" if T["dark"] else ""
    # heroStyle 결정
    if st.session_state.concept == "custom" and st.session_state.custom_theme:
        T["heroStyle"] = st.session_state.custom_theme.get("heroStyle","split")
    else:
        T["heroStyle"] = THEMES.get(st.session_state.concept,{}).get("heroStyle","split")
    mp = {"banner":sec_banner,"intro":sec_intro,"why":sec_why,"curriculum":sec_curriculum,
          "target":sec_target,"reviews":sec_reviews,"faq":sec_faq,"cta":sec_cta,
          "event_overview":sec_event_overview,"event_benefits":sec_event_benefits,
          "event_deadline":sec_event_deadline,"fest_hero":sec_fest_hero,
          "fest_lineup":sec_fest_lineup,"fest_benefits":sec_fest_benefits,
          "fest_cta":sec_fest_cta,"custom_section":sec_custom}
    body = "\n".join(mp[s](d,cp,T) for s in secs if s in mp)
    ttl  = cp.get("bannerTitle", cp.get("festHeroTitle", d["purpose_label"]))
    return (f'<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"/>'
            f'<meta name="viewport" content="width=device-width,initial-scale=1.0"/>'
            f'<title>{d["name"]} {d["subject"]} · {ttl}</title>'
            f'<link rel="preconnect" href="https://fonts.googleapis.com"/>'
            f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>'
            f'<link href="{T["fonts"]}" rel="stylesheet"/>'
            f'<style>:root{{{T["vars"]}}}{BASE_CSS}{T["extra_css"]}{dc}</style>'
            f'</head><body>{body}'
            f'<script>const ro=new IntersectionObserver(es=>{{es.forEach(e=>{{if(e.isIntersecting){{e.target.classList.add("on");ro.unobserve(e.target);}}}});}},{{threshold:.06}});document.querySelectorAll(".rv").forEach(el=>ro.observe(el));</script>'
            f'</body></html>')

# ══════════════════════════════════════
# UI CSS
# ══════════════════════════════════════
st.markdown("""<style>
/* 전체 배경 */
[data-testid="stSidebar"]{background:#08090F;border-right:1px solid #1A1F2E;}
/* 사이드바 텍스트 */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span:not(.stCheckbox span),
[data-testid="stSidebar"] .stCaption{color:#A0AABB!important;font-size:12px!important;}
/* 사이드바 제목 */
[data-testid="stSidebar"] h3{color:#E8EDF5!important;font-size:16px!important;font-weight:800!important;}
/* 구분선 */
[data-testid="stSidebar"] hr{border-color:#1A2035!important;}
/* 버튼 기본 */
.stButton>button{
    border-radius:8px!important;font-weight:700!important;
    border:1px solid #2A3450!important;
    background:#111828!important;color:#9AAAC8!important;
    transition:all .15s!important;font-size:12px!important;
}
.stButton>button:hover{background:#1A2640!important;color:#C8D4EA!important;border-color:#3A4860!important;}
/* Primary 버튼 */
.stButton>button[kind="primary"]{
    background:linear-gradient(135deg,#FF6B35,#E84393)!important;
    color:#fff!important;border:none!important;
}
/* 메트릭 */
div[data-testid="stMetric"]{
    background:#0B0F1C;border:1px solid #1E2640;
    border-radius:10px;padding:14px;
}
div[data-testid="stMetric"] label{color:#5A6A88!important;font-size:11px!important;}
div[data-testid="stMetric"] div{color:#E8EDF5!important;font-weight:700!important;}
/* 텍스트 입력 */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] select{
    background:#0B0F1C!important;
    border:1px solid #1E2640!important;
    color:#C8D4EA!important;
    border-radius:8px!important;
    font-size:12px!important;
}
/* 메인 영역 배경 */
.stMainBlockContainer{background:#0D1117;color:#E8EDF5;}
/* 메인 영역 기본 텍스트 색상 강제 */
.stMainBlockContainer p, .stMainBlockContainer span,
.stMainBlockContainer label, .stMainBlockContainer div {color:#C8D4EA;}
.stMainBlockContainer h1,.stMainBlockContainer h2,
.stMainBlockContainer h3,.stMainBlockContainer h4{color:#E8EDF5!important;}
.stMarkdown{color:#C8D4EA!important;}
/* 성공/정보 메시지 */
.stSuccess{background:rgba(52,211,153,.08)!important;border:1px solid rgba(52,211,153,.2)!important;}
.stInfo{background:rgba(99,102,241,.08)!important;border:1px solid rgba(99,102,241,.2)!important;}
.stError{background:rgba(248,113,113,.08)!important;border:1px solid rgba(248,113,113,.2)!important;}
/* 섹션 헤더 */
.section-header{
    font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
    color:#4A5878;padding:10px 16px 6px;
}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════
with st.sidebar:
    st.markdown("### 🎓 강사 페이지 빌더 Pro")
    st.caption("수능 강사 랜딩페이지 AI 생성기")
    st.divider()

    # ── API Key ──
    st.markdown('<div class="section-header">🔑 GROQ API KEY</div>', unsafe_allow_html=True)
    api_in = st.text_input("API Key", type="password", value=st.session_state.api_key,
                           placeholder="gsk_...", label_visibility="collapsed")
    if api_in != st.session_state.api_key:
        st.session_state.api_key = api_in
    if st.session_state.api_key:
        st.success("✓ Groq API 키 입력됨 (완전 무료)", icon="✅")
    else:
        st.markdown('<a href="https://console.groq.com" target="_blank" style="font-size:11px;color:#6A7A9A">👆 console.groq.com → API Keys → Create</a>', unsafe_allow_html=True)

    st.divider()

    # ── 페이지 목적 ──
    st.markdown('<div class="section-header">📋 페이지 목적</div>', unsafe_allow_html=True)
    pt = st.radio("목적", list(PURPOSE_SECTIONS.keys()),
                  index=list(PURPOSE_SECTIONS.keys()).index(st.session_state.purpose_type),
                  label_visibility="collapsed", horizontal=False)
    if pt != st.session_state.purpose_type:
        st.session_state.purpose_type = pt
        st.session_state.active_sections = PURPOSE_SECTIONS[pt].copy()
        st.session_state.custom_copy = None
        st.rerun()
    st.caption(PURPOSE_HINTS[pt])

    st.divider()

    # ── 페이지 컨셉 ──
    st.markdown('<div class="section-header">🎨 페이지 컨셉</div>', unsafe_allow_html=True)

    if st.button("🎲 AI 랜덤 생성 — 매번 완전히 새 디자인!", type="primary", use_container_width=True):
        if not st.session_state.api_key:
            st.warning("API 키를 먼저 입력해주세요")
        else:
            seed = random.choice(RANDOM_SEEDS)
            while len(RANDOM_SEEDS) > 1 and seed == st.session_state.last_seed:
                seed = random.choice(RANDOM_SEEDS)
            st.session_state.last_seed = seed
            with st.spinner(f"'{seed['mood'][:20]}...' 생성 중..."):
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

    mood_in = st.text_area("직접 묘사:", height=70, value=st.session_state.ai_mood,
                           placeholder="예: 관중이 가득찬 야구장 밤\n예: 사이버펑크 네온사인 다크 도시",
                           label_visibility="visible")
    st.session_state.ai_mood = mood_in

    if st.button("✦ 이 무드로 생성", use_container_width=True):
        if not mood_in.strip():
            st.warning("무드를 입력해주세요")
        elif not st.session_state.api_key:
            st.warning("API 키를 먼저 입력해주세요")
        else:
            with st.spinner("AI 컨셉 + 배경 이미지 생성 중..."):
                try:
                    r = gen_concept({"mood":mood_in.strip(),"layout":"auto","font":"auto"})
                    st.session_state.custom_theme = r
                    st.session_state.concept = "custom"
                    bg = build_bg_url(mood_in.strip())
                    st.session_state.bg_photo_url = bg
                    st.success(f"✓ '{r.get('name','새 컨셉')}' + 배경 이미지 생성됨!")
                    st.rerun()
                except Exception as e:
                    st.error(f"실패: {e}")

    # 프리셋
    st.caption("프리셋:")
    cols = st.columns(2)
    for i, (k, t) in enumerate(THEMES.items()):
        with cols[i % 2]:
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
        st.success(f"✦ {ct.get('name','AI 커스텀')}", icon="🎨")
        if st.session_state.bg_photo_url:
            st.caption(f"🖼 배경 이미지 적용됨")

    st.divider()

    # ── 강사 정보 ──
    st.markdown('<div class="section-header">👤 강사 정보</div>', unsafe_allow_html=True)
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
                        if p.get("slogan"):
                            st.caption(f'💬 "{p["slogan"]}"')
                        methods = [m for m in (p.get("signatureMethods") or []) if m and m != "없음"]
                        if methods:
                            st.caption(f'📚 학습법: {", ".join(methods)}')
                        if p.get("teachingStyle"):
                            st.caption(f'🎯 {p["teachingStyle"][:45]}')
                    else:
                        st.info("정보를 찾지 못했습니다.")
                except Exception as e:
                    st.error(f"검색 실패: {e}")

    st.divider()

    # ── 설정 ──
    st.markdown('<div class="section-header">📝 강의 브랜드명</div>', unsafe_allow_html=True)
    pl = st.text_input("브랜드명", value=st.session_state.purpose_label,
                       placeholder="2026 수능 파이널 완성", label_visibility="collapsed")
    st.session_state.purpose_label = pl

    st.markdown('<div class="section-header">🎯 수강 대상</div>', unsafe_allow_html=True)
    tgt = st.radio("대상", ["고3·N수","고1·2 — 기초 완성"],
                   horizontal=True, label_visibility="collapsed")
    st.session_state.target = tgt

    st.divider()

    # ── 섹션 ──
    st.markdown('<div class="section-header">📑 섹션 ON/OFF</div>', unsafe_allow_html=True)
    for sid in PURPOSE_SECTIONS[st.session_state.purpose_type]:
        chk = st.checkbox(SEC_LABELS.get(sid,sid),
                          value=sid in st.session_state.active_sections, key=f"sec_{sid}")
        if chk and sid not in st.session_state.active_sections:
            st.session_state.active_sections.append(sid)
        elif not chk and sid in st.session_state.active_sections:
            st.session_state.active_sections.remove(sid)

    # 기타 섹션
    st.markdown("---")
    csec_on = st.checkbox("✏️ 기타 섹션 추가", value=st.session_state.custom_section_on, key="chk_cs")
    st.session_state.custom_section_on = csec_on
    if csec_on:
        if "custom_section" not in st.session_state.active_sections:
            st.session_state.active_sections.append("custom_section")
        ct_in = st.text_input("섹션 주제", value=st.session_state.custom_section_topic,
                              placeholder="예: 수강평 이벤트, 합격 후기, 공지사항",
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

# ══════════════════════════════════════
# MAIN
# ══════════════════════════════════════
ordered = [s for s in PURPOSE_SECTIONS[st.session_state.purpose_type]
           if s in st.session_state.active_sections]
if st.session_state.custom_section_on and "custom_section" not in ordered:
    if st.session_state.custom_copy and st.session_state.custom_copy.get("custom_section_data"):
        ordered.append("custom_section")

final_html = build_html(ordered)
T_now = get_theme()

L, R = st.columns([1, 2], gap="large")

with L:
    # ── AI 문구 생성 ──
    st.markdown("### ✍️ AI 문구 생성")
    st.caption(PURPOSE_HINTS[st.session_state.purpose_type])
    ph_map = {
        "신규 커리큘럼": "예: 2026 수능 영어 파이널 완성. 고3·N수 대상. 선티 선생님의 씽킹맵 방법론.",
        "이벤트":       "예: 6월 모의고사 대비 특강. 3주 한정. 수강료 할인.",
        "기획전":       "예: 2026 영어 기획전. 독해·EBS·어법·파이널 4인 강사 통합 패키지.",
    }
    ctx = st.text_area("페이지 맥락", height=100,
                       placeholder=ph_map.get(st.session_state.purpose_type,"맥락 입력"),
                       help="강사 고유 특성이 있으면 자동으로 문구에 반영됩니다.")

    if st.button(f"✦ {st.session_state.purpose_type} 문구 AI 생성", type="primary", use_container_width=True):
        if not ctx.strip():
            st.warning("페이지 맥락을 입력해주세요")
        elif not st.session_state.api_key:
            st.warning("API 키를 먼저 입력해주세요")
        else:
            with st.spinner(f"문구 생성 중... (10~20초)"):
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

    # ── 섹션별 재생성 ──
    st.markdown("### 🎲 섹션별 문구 랜덤 재생성")
    st.caption("버튼 클릭 시 해당 섹션 문구만 새롭게 바뀝니다")
    regen_secs = [s for s in ordered if s in SEC_LABELS and s not in ("custom_section",)]
    # 섹션별 재생성 — 이모지만 사용해서 한 줄에 표시
    SEC_SHORT = {
        "banner":"배너","intro":"소개","why":"이유","curriculum":"커리큘럼",
        "target":"대상","reviews":"수강평","faq":"FAQ","cta":"CTA",
        "event_overview":"개요","event_benefits":"혜택","event_deadline":"마감",
        "fest_hero":"히어로","fest_lineup":"라인업","fest_benefits":"혜택","fest_cta":"CTA",
    }
    if regen_secs and st.session_state.api_key:
        # CSS로 버튼 크기 통일
        st.markdown("""<style>
        div[data-testid="stHorizontalBlock"] .stButton>button{
            font-size:11px!important;padding:6px 4px!important;
            white-space:nowrap!important;overflow:hidden!important;
            text-overflow:ellipsis!important;
        }
        </style>""", unsafe_allow_html=True)
        # 4열씩 묶어서 표시
        for row_start in range(0, len(regen_secs), 4):
            chunk = regen_secs[row_start:row_start+4]
            cols_r = st.columns(len(chunk))
            for i, sid in enumerate(chunk):
                label = SEC_SHORT.get(sid, sid)
                with cols_r[i]:
                    if st.button(f"🎲 {label}", key=f"regen_{sid}", use_container_width=True):
                        with st.spinner(f"{label} 재생성 중..."):
                            try:
                                r = gen_section(sid)
                                if st.session_state.custom_copy is None:
                                    st.session_state.custom_copy = {}
                                st.session_state.custom_copy.update(r)
                                st.rerun()
                            except Exception as e:
                                st.error(f"실패: {e}")
    elif not st.session_state.api_key:
        st.caption("API 키를 입력하면 버튼이 활성화됩니다.")

    st.divider()

    # ── 문구 직접 편집 ──
    st.markdown("### ✏️ 문구 직접 편집")
    if st.session_state.custom_copy:
        cp = st.session_state.custom_copy
        if st.session_state.purpose_type == "신규 커리큘럼":
            with st.expander("🏠 배너"):
                bt = st.text_input("메인 제목", value=cp.get("bannerTitle",""), key="ebt")
                bl = st.text_area("리드 문구", value=cp.get("bannerLead",""), height=55, key="ebl")
                cc_ = st.text_input("버튼 텍스트", value=cp.get("ctaCopy",""), key="ecc")
                if st.button("적용", key="ab"):
                    st.session_state.custom_copy.update({"bannerTitle":bt,"bannerLead":bl,"ctaCopy":cc_}); st.rerun()
            with st.expander("👤 강사 소개"):
                it = st.text_input("소개 제목", value=cp.get("introTitle",""), key="eit")
                id_ = st.text_area("소개 본문", value=cp.get("introDesc",""), height=55, key="eid")
                if st.button("적용", key="ai_"):
                    st.session_state.custom_copy.update({"introTitle":it,"introDesc":id_}); st.rerun()
        elif st.session_state.purpose_type == "이벤트":
            with st.expander("📅 이벤트 개요"):
                etl = st.text_input("이벤트 제목", value=cp.get("eventTitle",""), key="eetl")
                edesc = st.text_area("이벤트 설명", value=cp.get("eventDesc",""), height=55, key="eedesc")
                if st.button("적용", key="aev"):
                    st.session_state.custom_copy.update({"eventTitle":etl,"eventDesc":edesc}); st.rerun()
        elif st.session_state.purpose_type == "기획전":
            with st.expander("🏆 기획전 히어로"):
                fht = st.text_input("기획전 제목", value=cp.get("festHeroTitle",""), key="efht")
                fhc = st.text_input("서브 카피", value=cp.get("festHeroCopy",""), key="efhc")
                if st.button("적용", key="afh"):
                    st.session_state.custom_copy.update({"festHeroTitle":fht,"festHeroCopy":fhc}); st.rerun()
        ctk = "festCtaTitle" if st.session_state.purpose_type=="기획전" else "ctaTitle"
        csk = "festCtaSub"   if st.session_state.purpose_type=="기획전" else "ctaSub"
        with st.expander("📣 CTA"):
            ct_ = st.text_area("CTA 제목", value=cp.get(ctk,""), height=55, key="ect")
            cs_ = st.text_input("서브문구", value=cp.get(csk,""), key="ecs")
            if st.button("적용", key="ac"):
                st.session_state.custom_copy.update({ctk:ct_,csk:cs_}); st.rerun()
    else:
        st.caption("AI로 문구를 생성하면 여기서 직접 수정할 수 있습니다.")

    st.divider()

    # ── HTML 내보내기 ──
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
    with m2: st.metric("목적", st.session_state.purpose_type)
    with m3: st.metric("섹션 수", len(ordered))
    import streamlit.components.v1 as components
    components.html(final_html, height=900, scrolling=True)
