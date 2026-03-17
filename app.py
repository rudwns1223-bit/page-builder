"""
강사 페이지 빌더 Pro v6.1 (이미지 압축 & 가독성 최적화)
"""
import streamlit as st
import requests
import json, re, time, random
import base64
from io import BytesIO
from PIL import Image

st.set_page_config(
    page_title="강사 페이지 빌더 Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════
# SESSION STATE 초기화
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
    "uploaded_bg_b64": "",
}
for _k, _v in _D.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

if not st.session_state.api_key:
    try: st.session_state.api_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception: pass

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
    {"mood":"관중이 가득찬 야구장, 밤의 전광판 붉은빛","layout":"brutalist","font":"display"},
    {"mood":"오래된 수학 교실 분필 칠판 먼지 냄새","layout":"editorial","font":"mono"},
    {"mood":"축구공이 돋보이는 축구장 잔디밭","layout":"immersive","font":"display","particle_hint":"none"},
    {"mood":"겨울 새벽 눈 덮인 사찰 고요 집중 먹빛","layout":"minimal","font":"serif","particle_hint":"snow"},
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

# 배경 이미지 키워드 맵 (축구장/야구장 추가)
KO_BG = {
    "축구공": "soccer ball field grass stadium",
    "축구장": "soccer stadium crowd night field",
    "축구": "soccer stadium grass sports",
    "야구장": "baseball stadium crowd night lights",
    "야구": "baseball game crowd stadium",
    "경기장": "sports arena stadium crowd",
    "밤": "night dark dramatic",
    "새벽": "dawn morning light",
    "도서관": "library books dark wooden",
    "책": "books library study",
    "교실": "classroom chalkboard",
    "도시": "city urban skyline",
    "우주": "space cosmos galaxy",
    "오로라": "aurora borealis northern lights",
    "바다": "ocean sea dramatic",
    "숲": "forest trees nature",
    "단풍": "autumn leaves fall",
    "벚꽃": "cherry blossom spring",
    "겨울": "winter snow cold",
    "사막": "desert sand golden",
}

# ══════════════════════════════════════
# 유틸
# ══════════════════════════════════════
def strip_hanja(text: str) -> str:
    if not isinstance(text, str): return str(text) if text is not None else ""
    result = []
    for ch in text:
        cp = ord(ch)
        if 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or 0x20000 <= cp <= 0x2A6DF: continue
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
    if not mood: return ""
    text = mood.lower()
    found = []
    for ko, en in sorted(KO_BG.items(), key=lambda x: -len(x[0])):
        if ko.lower() in text:
            found.extend(en.split())
            text = text.replace(ko.lower(), " ")
            if len(found) >= 6: break
    eng = [w for w in re.findall(r"[a-zA-Z]{4,}", mood) if w.lower() not in ("this","that","with","from","have","been","just","very")]
    found.extend(eng[:3])
    if not found: found = ["stadium","crowd","sports","night"]
    tags = ",".join(list(dict.fromkeys(found))[:3])
    lock = random.randint(1, 99999)
    return f"https://loremflickr.com/1920/900/{tags}?lock={lock}"

# ══════════════════════════════════════
# AI 호출
# ══════════════════════════════════════
def call_ai(prompt: str, system: str = "", max_tokens: int = 2000) -> str:
    key = st.session_state.api_key.strip()
    if not key: raise ValueError("API 키가 없습니다. 사이드바에서 gsk_... 키를 입력해주세요.")
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
        if resp.status_code == 401: raise Exception("🔑 API 키 오류 — console.groq.com에서 확인해주세요.")
        if resp.status_code == 429: last_err = Exception(f"⏳ 한도 초과 ({model})"); time.sleep(2); continue
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

다음 JSON만 반환 (한 줄, 줄바꿈 없음):
{{"name":"2-4글자이름","dark":true,"heroStyle":"immersive","c1":"#hex","c2":"#hex","c3":"#hex","c4":"#hex","bg":"#hex","bg2":"#hex","bg3":"#hex","textHex":"#hex","textRgb":"r,g,b","bdAlpha":"rgba(r,g,b,.12)","displayFont":"Google Font","bodyFont":"Noto Sans KR","fontWeights":"400;700;900","displayFontWeights":"400;700","borderRadiusPx":8,"btnBorderRadiusPx":100,"particle":"none","ctaGradient":"linear-gradient(135deg,#hex,#hex)","extraCSS":"CSS min 120 chars single quotes only"}}"""
    # 🌟 max_tokens를 2000으로 늘려 중간에 잘리는 오류 방지
    result = safe_json(call_ai(prompt, max_tokens=2000))
    
    name = result.get("name","")
    generic = ["한국","교육","랜딩","페이지","강사","수능","학습","공부","스터디","강의"]
    if not name or any(g in name for g in generic) or len(name) > 12:
        mood_word = seed.get("mood","").split()[0][:4] if seed.get("mood") else "새 컨셉"
        result["name"] = mood_word + " 🎨"
    if seed.get("particle_hint") and result.get("particle","none") == "none":
        result["particle"] = seed["particle_hint"]
    return result

def _get_instructor_context() -> str:
    ip = st.session_state.get("inst_profile") or {}
    name = st.session_state.instructor_name
    subj = st.session_state.subject
    if not ip.get("found") or not name: return f"강사명: {name} | 과목: {subj}" if name else f"과목: {subj}"
    parts = [f"강사: {name} ({subj})"]
    if ip.get("bio"): parts.append(f"이력: {ip['bio']}")
    if ip.get("slogan"): parts.append(f"슬로건: \"{ip['slogan']}\"")
    methods = [m for m in (ip.get("signatureMethods") or []) if m and m != "없음"]
    if methods: parts.append(f"고유 학습법: {', '.join(methods)}")
    return "\n".join(parts)

def gen_copy(ctx: str, ptype: str, tgt: str, plabel: str) -> dict:
    inst_ctx = _get_instructor_context()
    schemas = {
        "신규 커리큘럼": '{"bannerSub":"10자이내","bannerTitle":"20자이내","bannerLead":"40-60자 수험생 심리 자극 문구","ctaCopy":"10자이내","ctaTitle":"CTA 제목","ctaSub":"30자이내","ctaBadge":"15자이내","statBadges":[],"introTitle":"20자이내","introDesc":"50-80자 강사 차별점","introBio":"강사 학습법 포함 40자이내","introBadges":[],"whyTitle":"20자이내","whySub":"30자이내","whyReasons":[["이모지","12자제목","45자구체설명"],["이모지","12자","45자"],["이모지","12자","45자"]],"curriculumTitle":"20자이내","curriculumSub":"30자이내","curriculumSteps":[["01","8자","각 단계 학생에게 필요한 이유 20자","기간"],["02","8자","20자","기간"],["03","8자","20자","기간"],["04","8자","20자","기간"]],"targetTitle":"20자이내","targetItems":["25자이내","항목2","항목3","항목4"],"reviews":[["30자이내 구체적 변화 인용문","이름","변화뱃지"],["인용문","이름","뱃지"],["인용문","이름","뱃지"]],"faqs":[["구체적 질문15자","답변40자"],["질문","답변"],["질문","답변"]]}',
        "이벤트": '{"bannerSub":"10자","bannerTitle":"20자","bannerLead":"50자 긴박감","ctaCopy":"10자","ctaTitle":"CTA","ctaSub":"30자","ctaBadge":"15자","statBadges":[],"eventTitle":"20자","eventDesc":"40자","eventDetails":[["📅","이벤트 기간","날짜"],["🎯","대상","값"],["💰","혜택","값"]],"benefitsTitle":"20자","eventBenefits":[{"icon":"이모지","title":"혜택명","desc":"35자","badge":"8자","no":"01"},{"icon":"이모지","title":"혜택명","desc":"35자","badge":"8자","no":"02"},{"icon":"이모지","title":"혜택명","desc":"35자","badge":"8자","no":"03"}],"deadlineTitle":"20자","deadlineMsg":"60자 긴박감","reviews":[["30자 인용문","이름","뱃지"],["인용문","이름","뱃지"],["인용문","이름","뱃지"]]}',
        "기획전": '{"festHeroTitle":"20자","festHeroCopy":"30자","festHeroSub":"40자","festHeroStats":[["수치","라벨"],["수치","라벨"],["수치","라벨"],["수치","라벨"]],"festLineupTitle":"20자","festLineupSub":"40자","festLineup":[{"name":"강사명","tag":"분야8자","tagline":"30자","badge":"8자","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"소개","badge":"뱃지","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"소개","badge":"뱃지","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"소개","badge":"뱃지","emoji":"이모지"}],"festBenefitsTitle":"20자","festBenefits":[{"icon":"이모지","title":"혜택명","desc":"35자","badge":"8자","no":"01"},{"icon":"이모지","title":"혜택명","desc":"35자","badge":"8자","no":"02"},{"icon":"이모지","title":"혜택명","desc":"35자","badge":"8자","no":"03"},{"icon":"이모지","title":"혜택명","desc":"35자","badge":"8자","no":"04"}],"festCtaTitle":"CTA제목","festCtaSub":"40자"}',
    }
    prompt = f"""대한민국 최고 수능 교육 랜딩페이지 카피라이터.
맥락: "{ctx}" | 목적: {ptype} | 대상: {tgt} | 브랜드: {plabel} | 강사: {inst_ctx}
JSON만 반환 (줄바꿈 없이): {schemas.get(ptype, schemas['신규 커리큘럼'])}"""
    return safe_json(call_ai(prompt, max_tokens=2500))

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
# BASE CSS (가독성 향상을 위해 그림자 효과 강화)
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
                "btn_s":"","top_brd":"var(--bd)","blur":"","shadow":""}
    
    # 🌟 이미지 배경 시 가독성 해결: 어두운 오버레이 + 텍스트 이중 그림자
    return {"hero_bg":f"background:var(--bg) url('{bg_url}') center/cover no-repeat",
            "overlay":'<div style="position:absolute;inset:0;background:rgba(0,0,0,0.65);z-index:1;pointer-events:none"></div>',
            "tc":"color:#fff","t70c":"color:rgba(255,255,255,.9)",
            "c1c":"#fff","bdc":"rgba(255,255,255,.3)",
            "card_bg":"rgba(0,0,0,.65)",
            "btn_s":"color:#fff;border-color:rgba(255,255,255,.6)",
            "top_brd":"rgba(255,255,255,.2)","blur":"backdrop-filter:blur(12px);",
            "shadow":"text-shadow: 0 4px 20px rgba(0,0,0,0.9), 0 1px 3px rgba(0,0,0,1);"}

def sec_banner(d, cp, T):
    sub    = strip_hanja(cp.get("bannerSub", d["subject"]+" 완성"))
    title  = strip_hanja(cp.get("bannerTitle", d["purpose_label"]))
    lead   = strip_hanja(cp.get("bannerLead", f"{d['target']}을 위한 커리큘럼"))
    cta    = strip_hanja(cp.get("ctaCopy", "수강신청하기"))
    stats  = cp.get("statBadges", [])
    
    # 🌟 Base64 이미지가 있으면 최우선 적용
    bg_url = st.session_state.get("uploaded_bg_b64") or cp.get("bg_photo_url", "")
    
    hs     = T.get("heroStyle", "split")
    s      = _bg(bg_url, T["dark"])

    kh = "".join(f'<span style="font-size:9.5px;font-weight:700;padding:5px 12px;border-radius:var(--r-btn,100px);color:{s["c1c"]};border:1px solid {s["bdc"]};margin:2px;{s["shadow"]}">{k}</span>' for k in ["개념","기출","실전","파이널"])
    sh = "".join(f'<div><div style="font-family:var(--fh);font-size:clamp(18px,2.8vw,26px);font-weight:900;color:{s["c1c"]};{s["shadow"]}">{sv}</div><div style="font-size:9px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;{s["t70c"]};margin-top:2px;{s["shadow"]}">{sl}</div></div>' for sv,sl in stats) if stats else ""

    if hs == "immersive":
        return (
            f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:flex;flex-direction:column;justify-content:flex-end">'
            + s["overlay"] +
            '<div style="position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.88) 0%,rgba(0,0,0,.15) 65%,transparent 100%);z-index:1;pointer-events:none"></div>'
            f'<div style="position:relative;z-index:2;padding:clamp(48px,7vw,80px) clamp(32px,6vw,88px);max-width:860px">'
            f'<div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.12);{s["blur"]}padding:5px 16px;border-radius:100px;margin-bottom:20px;border:1px solid rgba(255,255,255,.2);font-size:10px;font-weight:700;color:#fff;letter-spacing:.14em;text-transform:uppercase;{s["shadow"]}">{sub}</div>'
            f'<h1 style="font-family:var(--fh);font-size:clamp(52px,8vw,110px);font-weight:900;line-height:.85;letter-spacing:-.05em;color:#fff;margin-bottom:18px;{s["shadow"]}" class="st">{title}</h1>'
            f'<p style="font-size:clamp(14px,1.6vw,17px);line-height:1.85;color:rgba(255,255,255,.9);max-width:520px;margin-bottom:24px;{s["shadow"]}">{lead}</p>'
            f'<div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:24px">{kh}</div>'
            f'<div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:22px">'
            f'<a class="btn-p" href="#" style="box-shadow:0 0 28px rgba(255,255,255,.12)">{cta} →</a>'
            f'<a href="#" style="display:inline-flex;align-items:center;gap:7px;background:rgba(255,255,255,.1);{s["blur"]}color:#fff;font-weight:600;padding:13px 28px;border-radius:100px;border:1.5px solid rgba(255,255,255,.3);font-size:14px;text-decoration:none;{s["shadow"]}">강의 미리보기</a></div>'
            + (f'<div style="display:flex;gap:36px;margin-top:40px;padding-top:24px;border-top:1px solid rgba(255,255,255,.2)">{sh}</div>' if sh else "")
            + '</div></section>'
        )
    else:  # split or editorial
        ci = "".join(f'<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid {s["bdc"]}"><span style="font-size:11px;font-weight:600;{s["t70c"]};{s["shadow"]}">{l}</span><span style="font-size:11.5px;font-weight:700;{s["tc"]};{s["shadow"]}">{v}</span></div>' for l,v in [["대상",d["target"]],["과목",d["subject"]],["목적",d["purpose_label"][:14]+"…"]])
        return (
            f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:grid;grid-template-columns:1fr 360px">'
            + s["overlay"] +
            f'<div style="position:relative;z-index:2;display:flex;flex-direction:column;justify-content:center;padding:clamp(60px,8vw,100px) clamp(24px,4vw,52px) clamp(60px,8vw,100px) clamp(32px,6vw,88px)">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:28px"><div style="width:32px;height:2px;background:{s["c1c"]}"></div><span style="font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;{s["tc"]};{s["shadow"]}">{sub}</span></div>'
            f'<h1 style="font-family:var(--fh);font-size:clamp(40px,6vw,84px);font-weight:900;line-height:.88;letter-spacing:-.05em;{s["tc"]};{s["shadow"]}" class="st">{title}</h1>'
            f'<p style="font-size:clamp(13px,1.4vw,15.5px);line-height:2;{s["t70c"]};margin-top:20px;max-width:420px;padding-left:14px;border-left:2px solid {s["c1c"]};{s["shadow"]}">{lead}</p>'
            f'<div style="display:flex;gap:5px;flex-wrap:wrap;margin-top:18px">{kh}</div>'
            f'<div style="display:flex;gap:12px;margin-top:26px"><a class="btn-p" href="#">{cta} →</a><a class="btn-s" href="#" style="{s["btn_s"]};{s["shadow"]}">강의 미리보기</a></div>'
            + (f'<div style="display:flex;gap:28px;margin-top:48px;padding-top:24px;border-top:1px solid {s["top_brd"]}">{sh}</div>' if sh else "")
            + f'</div>'
            f'<div style="background:rgba(0,0,0,.18);border-left:1px solid {s["bdc"]};display:flex;align-items:center;justify-content:center;padding:48px 24px;position:relative;z-index:2">'
            f'<div style="width:100%;background:{s["card_bg"]};border:1px solid {s["bdc"]};border-radius:var(--r,12px);overflow:hidden;{s["blur"]}">'
            f'<div style="background:var(--c1);padding:18px 22px;text-align:center"><div style="font-family:var(--fh);font-size:19px;font-weight:900;color:#fff;line-height:1.25;text-shadow:0 2px 8px rgba(0,0,0,0.5)">{title}</div></div>'
            f'<div style="padding:18px 22px">{ci}<a class="btn-p" href="#" style="width:100%;justify-content:center;margin-top:14px;display:flex">{cta} →</a></div>'
            f'</div></div></section>'
        )

# 나머지 섹션 빌더 함수들 (변경 없음)
def sec_intro(d, cp, T): return f'<section class="sec alt" id="intro"><div class="rv"><div class="tag-line">소개</div><h2 class="sec-h2 st">{cp.get("introTitle","소개")}</h2><p class="sec-sub">{cp.get("introDesc","")}</p></div></section>'
def sec_why(d, cp, T): return f'<section class="sec" id="why"><div class="rv"><div class="tag-line">이유</div><h2 class="sec-h2 st">{cp.get("whyTitle","필요한 이유")}</h2></div></section>'
def sec_curriculum(d, cp, T): return f'<section class="sec alt" id="curriculum"><div class="rv"><div class="tag-line">커리큘럼</div><h2 class="sec-h2 st">{cp.get("curriculumTitle","커리큘럼")}</h2></div></section>'
def sec_target(d, cp, T): return f'<section class="sec" id="target"><div class="rv"><div class="tag-line">대상</div><h2 class="sec-h2 st">{cp.get("targetTitle","대상")}</h2></div></section>'
def sec_reviews(d, cp, T): return f'<section class="sec alt" id="reviews"><div class="rv"><div class="tag-line">수강평</div><h2 class="sec-h2 st">수강평</h2></div></section>'
def sec_faq(d, cp, T): return f'<section class="sec" id="faq"><div class="rv"><div class="tag-line">FAQ</div><h2 class="sec-h2 st">FAQ</h2></div></section>'
def sec_cta(d, cp, T): return f'<section style="padding:80px;text-align:center;background:{T["cta"]}"><h2 style="font-family:var(--fh);font-size:36px;color:#fff">{cp.get("ctaTitle","시작하세요")}</h2></section>'
def sec_event_overview(d, cp, T): return f'<section class="sec" id="ev-ov"><h2 class="sec-h2 st">{cp.get("eventTitle","이벤트")}</h2></section>'
def sec_event_benefits(d, cp, T): return f'<section class="sec alt" id="ev-bn"><h2 class="sec-h2 st">이벤트 혜택</h2></section>'
def sec_event_deadline(d, cp, T): return f'<section class="sec" id="ev-dl"><h2 class="sec-h2 st">마감 임박</h2></section>'
def sec_fest_hero(d, cp, T): return f'<section style="padding:100px;text-align:center;background:{T["cta"]}"><h1 style="color:#fff;font-size:60px">{cp.get("festHeroTitle","기획전")}</h1></section>'
def sec_fest_lineup(d, cp, T): return f'<section class="sec"><h2 class="sec-h2 st">라인업</h2></section>'
def sec_fest_benefits(d, cp, T): return f'<section class="sec alt"><h2 class="sec-h2 st">기획전 혜택</h2></section>'
def sec_fest_cta(d, cp, T): return f'<section style="padding:80px;text-align:center;background:{T["cta"]}"><h2 style="color:#fff">신청하기</h2></section>'
def sec_custom(d, cp, T): return ""

def _particle_js(p): return ""

def build_html(secs: list) -> str:
    T  = get_theme()
    cp = dict(st.session_state.custom_copy or {})
    # 배경 이미지 우선순위: 1순위 업로드된 base64, 2순위 자동 URL
    if st.session_state.get("uploaded_bg_b64"):
        cp["bg_photo_url"] = st.session_state.uploaded_bg_b64
    elif st.session_state.bg_photo_url:
        cp["bg_photo_url"] = st.session_state.bg_photo_url
        
    d  = {"name": st.session_state.instructor_name or "강사", "subject": st.session_state.subject, "purpose_label": st.session_state.purpose_label, "target": st.session_state.target}
    mp = {"banner":sec_banner,"intro":sec_intro,"why":sec_why,"curriculum":sec_curriculum,
          "target":sec_target,"reviews":sec_reviews,"faq":sec_faq,"cta":sec_cta,
          "event_overview":sec_event_overview,"event_benefits":sec_event_benefits,
          "event_deadline":sec_event_deadline,"fest_hero":sec_fest_hero,
          "fest_lineup":sec_fest_lineup,"fest_benefits":sec_fest_benefits,
          "fest_cta":sec_fest_cta,"custom_section":sec_custom}
    body = "\n".join(mp[s](d,cp,T) for s in secs if s in mp)
    return (f'<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"/>'
            f'<link href="{T["fonts"]}" rel="stylesheet"/>'
            f'<style>:root{{{T["vars"]}}}{BASE_CSS}{T["extra_css"]}</style>'
            f'</head><body>{body}'
            f'<script>const ro=new IntersectionObserver(es=>{{es.forEach(e=>{{if(e.isIntersecting){{e.target.classList.add("on");ro.unobserve(e.target);}}}});}},{{threshold:.06}});document.querySelectorAll(".rv").forEach(el=>ro.observe(el));</script>'
            f'</body></html>')

# ══════════════════════════════════════
# UI CSS (사이드바 스타일)
# ══════════════════════════════════════
st.markdown("""<style>
[data-testid="stSidebar"]{background:#08090F;border-right:1px solid #1A1F2E;}
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,[data-testid="stSidebar"] span:not(.stCheckbox span),[data-testid="stSidebar"] .stCaption{color:#A0AABB!important;font-size:12px!important;}
[data-testid="stSidebar"] h3{color:#E8EDF5!important;font-size:16px!important;font-weight:800!important;}
.stButton>button{border-radius:8px!important;font-weight:700!important;border:1px solid #2A3450!important;background:#111828!important;color:#9AAAC8!important;transition:all .15s!important;font-size:12px!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#FF6B35,#E84393)!important;color:#fff!important;border:none!important;}
.section-header{font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#4A5878;padding:10px 16px 6px;}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════
with st.sidebar:
    st.markdown("### 🎓 강사 페이지 빌더 Pro")
    st.caption("수능 강사 랜딩페이지 AI 생성기")
    st.divider()

    st.markdown('<div class="section-header">🔑 GROQ API KEY</div>', unsafe_allow_html=True)
    api_in = st.text_input("API Key", type="password", value=st.session_state.api_key, label_visibility="collapsed")
    if api_in != st.session_state.api_key: st.session_state.api_key = api_in

    st.divider()

    st.markdown('<div class="section-header">📋 페이지 목적</div>', unsafe_allow_html=True)
    pt = st.radio("목적", list(PURPOSE_SECTIONS.keys()), index=list(PURPOSE_SECTIONS.keys()).index(st.session_state.purpose_type), label_visibility="collapsed")
    if pt != st.session_state.purpose_type:
        st.session_state.purpose_type = pt
        st.session_state.active_sections = PURPOSE_SECTIONS[pt].copy()
        st.rerun()

    st.divider()

    st.markdown('<div class="section-header">🎨 페이지 컨셉</div>', unsafe_allow_html=True)

    if st.button("🎲 AI 랜덤 생성", type="primary", use_container_width=True):
        if st.session_state.api_key:
            seed = random.choice(RANDOM_SEEDS)
            with st.spinner(f"'{seed['mood'][:20]}...' 생성 중..."):
                r = gen_concept(seed)
                st.session_state.custom_theme = r
                st.session_state.concept = "custom"
                st.session_state.bg_photo_url = build_bg_url(seed["mood"])
                st.session_state.uploaded_bg_b64 = "" 
                st.rerun()

    mood_in = st.text_area("직접 묘사:", height=70, value=st.session_state.ai_mood)
    st.session_state.ai_mood = mood_in

    if st.button("✦ 이 무드로 생성", use_container_width=True):
        if mood_in.strip() and st.session_state.api_key:
            with st.spinner("AI 컨셉 생성 중..."):
                r = gen_concept({"mood":mood_in.strip(),"layout":"auto","font":"auto"})
                st.session_state.custom_theme = r
                st.session_state.concept = "custom"
                st.session_state.bg_photo_url = build_bg_url(mood_in.strip())
                st.session_state.uploaded_bg_b64 = ""  
                st.rerun()

    # 🌟 이미지 업로드 로직 수정 (자동 압축 기능 적용)
    st.markdown("**🖼 배경 이미지 직접 업로드**")
    uploaded_img = st.file_uploader("배경 이미지", type=["jpg","jpeg","png","webp"], label_visibility="collapsed")
    if uploaded_img is not None:
        try:
            # 6.5MB 고화질 이미지로 인한 iframe 렌더링 뻗음 방지 (Pillow로 크기/용량 자동 압축)
            img = Image.open(uploaded_img)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=75)
            b64 = base64.b64encode(buffered.getvalue()).decode()
            st.session_state.uploaded_bg_b64 = f"data:image/jpeg;base64,{b64}"
            st.session_state.bg_photo_url = ""
            st.success("✓ 이미지 최적화 및 업로드 완료!")
        except Exception as e:
            st.error(f"이미지 처리 오류: {e}")
            
    if st.session_state.uploaded_bg_b64:
        if st.button("🗑 업로드 이미지 제거", use_container_width=True):
            st.session_state.uploaded_bg_b64 = ""
            st.rerun()

    cols = st.columns(2)
    for i, (k, t) in enumerate(THEMES.items()):
        with cols[i % 2]:
            if st.button(t["label"], key=f"th_{k}", type="primary" if st.session_state.concept == k else "secondary", use_container_width=True):
                st.session_state.concept = k
                st.session_state.custom_theme = None
                st.session_state.bg_photo_url = ""
                st.session_state.uploaded_bg_b64 = ""
                st.rerun()

# ══════════════════════════════════════
# MAIN 화면 구성
# ══════════════════════════════════════
ordered = [s for s in PURPOSE_SECTIONS[st.session_state.purpose_type] if s in st.session_state.active_sections]
final_html = build_html(ordered)

L, R = st.columns([1, 2], gap="large")

with L:
    st.markdown("### ✍️ AI 문구 생성")
    ctx = st.text_area("페이지 맥락", height=100)
    if st.button(f"✦ 문구 생성", type="primary", use_container_width=True) and st.session_state.api_key:
        with st.spinner("생성 중..."):
            st.session_state.custom_copy = gen_copy(ctx, st.session_state.purpose_type, st.session_state.target, st.session_state.purpose_label)
            st.rerun()

with R:
    st.markdown("### 👁 실시간 미리보기")
    import streamlit.components.v1 as components
    components.html(final_html, height=900, scrolling=True)
