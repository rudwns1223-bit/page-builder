"""
강사 페이지 빌더 Pro v6.2 (JSON 오류 완벽해결 & 이미지 압축)
"""
import streamlit as st
import requests
import json, re, time, random
import base64
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="강사 페이지 빌더 Pro", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

# ── SESSION STATE 초기화 ──
_D = {"api_key":"","concept":"sakura","custom_theme":None,"instructor_name":"","subject":"영어","purpose_label":"2026 수능 파이널 완성","purpose_type":"신규 커리큘럼","target":"고3·N수","custom_copy":None,"bg_photo_url":"","active_sections":["banner","intro","why","curriculum","cta"],"ai_mood":"","inst_profile":None,"last_seed":None,"custom_section_on":False,"custom_section_topic":"","uploaded_bg_b64":""}
for k, v in _D.items():
    if k not in st.session_state: st.session_state[k] = v

if not st.session_state.api_key:
    try: st.session_state.api_key = st.secrets.get("GROQ_API_KEY", "")
    except: pass

# ── 상수 및 프리셋 ──
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama3-70b-8192", "mixtral-8x7b-32768"]

THEMES = {
    "sakura": {"label":"🌸 벚꽃 봄","dark":False,"fonts":"https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;700&display=swap","vars":"--c1:#B5304A;--c2:#E89BB5;--c3:#F5CEDA;--c4:#2A111A;--bg:#FBF6F4;--bg2:#F7EFF1;--bg3:#F2E5E9;--text:#2A111A;--t70:rgba(42,17,26,.7);--t45:rgba(42,17,26,.45);--bd:rgba(42,17,26,.10);--fh:'Playfair Display','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:12px;--r-btn:100px;","extra_css":".st{font-style:italic}","cta":"linear-gradient(135deg,#2A111A,#B5304A)","heroStyle":"editorial"},
    "fire":   {"label":"🔥 다크 파이어","dark":True,"fonts":"https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@400;700;900&family=DM+Sans:wght@300;400;700&display=swap","vars":"--c1:#FF4500;--c2:#FF8C00;--c3:#FFD700;--c4:#0D0705;--bg:#0D0705;--bg2:#130A04;--bg3:#1A0E06;--text:#F1F5F9;--t70:rgba(241,245,249,.7);--t45:rgba(241,245,249,.45);--bd:rgba(255,69,0,.22);--fh:'Bebas Neue','Noto Sans KR',sans-serif;--fb:'DM Sans','Noto Sans KR',sans-serif;--r:4px;--r-btn:4px;","extra_css":".st{letter-spacing:.05em}","cta":"linear-gradient(135deg,#0D0705,#FF4500 60%,#FF8C00)","heroStyle":"immersive"},
    "ocean":  {"label":"🌊 오션 블루","dark":False,"fonts":"https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap","vars":"--c1:#0EA5E9;--c2:#38BDF8;--c3:#BAE6FD;--c4:#0C4A6E;--bg:#F0F9FF;--bg2:#E0F2FE;--bg3:#BAE6FD;--text:#0C1A2E;--t70:rgba(12,26,46,.7);--t45:rgba(12,26,46,.45);--bd:rgba(14,165,233,.15);--fh:'Syne','Noto Sans KR',sans-serif;--fb:'Noto Sans KR',sans-serif;--r:10px;--r-btn:100px;","extra_css":".st{font-weight:800}","cta":"linear-gradient(135deg,#0C4A6E,#0EA5E9)","heroStyle":"split"},
    "luxury": {"label":"✨ 골드 럭셔리","dark":True,"fonts":"https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,500;0,600;1,300;1,500&family=Noto+Serif+KR:wght@300;400;600&family=DM+Sans:wght@300;400;500&display=swap","vars":"--c1:#C8975A;--c2:#D4AF72;--c3:#EDD8A4;--c4:#0C0B09;--bg:#0C0B09;--bg2:#131108;--bg3:#1A1810;--text:#F5F0E8;--t70:rgba(245,240,232,.7);--t45:rgba(245,240,232,.45);--bd:rgba(200,151,90,.15);--fh:'Cormorant Garamond','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:2px;--r-btn:2px;","extra_css":".st{font-weight:300;font-style:italic}","cta":"linear-gradient(135deg,#0C0B09,#2A2010)","heroStyle":"editorial"},
    "cosmos": {"label":"🌌 코스모스","dark":True,"fonts":"https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Noto+Sans+KR:wght@300;400;700&family=DM+Sans:wght@300;400;500&display=swap","vars":"--c1:#7C3AED;--c2:#06B6D4;--c3:#A78BFA;--c4:#030712;--bg:#030712;--bg2:#080C18;--bg3:#0D1220;--text:#F1F5F9;--t70:rgba(241,245,249,.7);--t45:rgba(241,245,249,.45);--bd:rgba(124,58,237,.22);--fh:'Orbitron','Noto Sans KR',sans-serif;--fb:'DM Sans','Noto Sans KR',sans-serif;--r:0px;--r-btn:0px;","extra_css":".st{letter-spacing:.1em;text-transform:uppercase}","cta":"linear-gradient(135deg,#030712,#2D1B69)","heroStyle":"immersive"},
}

PURPOSE_SECTIONS = {
    "신규 커리큘럼": ["banner","intro","why","curriculum","target","reviews","faq","cta"],
    "이벤트": ["banner","event_overview","event_benefits","event_deadline","reviews","cta"],
    "기획전": ["fest_hero","fest_lineup","fest_benefits","fest_cta"],
}

KO_BG = {
    "축구공":"soccer ball field stadium","축구장":"soccer stadium crowd night field","축구":"soccer stadium grass sports",
    "야구장":"baseball stadium crowd night lights","야구":"baseball game crowd stadium",
    "경기장":"sports arena stadium crowd","밤":"night dark dramatic","새벽":"dawn morning light",
    "도서관":"library books dark wooden","책":"books library study","교실":"classroom chalkboard",
    "도시":"city urban skyline","우주":"space cosmos galaxy","별":"stars night sky",
    "오로라":"aurora borealis northern lights","바다":"ocean sea dramatic","숲":"forest trees nature",
    "단풍":"autumn leaves fall","벚꽃":"cherry blossom spring","겨울":"winter snow cold",
    "사막":"desert sand golden","이집트":"egypt pyramid desert","사찰":"temple korea traditional",
}

# ── 유틸 함수 ──
def strip_hanja(text: str) -> str:
    if not isinstance(text, str): return str(text) if text is not None else ""
    return "".join(c for c in text if not (0x4E00<=ord(c)<=0x9FFF or 0x3400<=ord(c)<=0x4DBF or 0x20000<=ord(c)<=0x2A6DF)).strip()

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
    try: return clean_obj(json.loads(s))
    except Exception as e:
        raise ValueError(f"JSON 파싱 실패: {e}\n원본: {raw[:300]}")

def build_bg_url(mood: str) -> str:
    if not mood: return ""
    text, found = mood.lower(), []
    for ko, en in sorted(KO_BG.items(), key=lambda x: -len(x[0])):
        if ko.lower() in text:
            found.extend(en.split()); text = text.replace(ko.lower(), " ")
            if len(found) >= 6: break
    eng = [w for w in re.findall(r"[a-zA-Z]{4,}", mood) if w.lower() not in ("this","that","with","from")]
    found.extend(eng[:3])
    if not found: found = ["stadium","crowd","sports","night"]
    tags = ",".join(list(dict.fromkeys(found))[:3])
    return f"https://loremflickr.com/1920/900/{tags}?lock={random.randint(1,99999)}"

# ── AI 호출 ──
def call_ai(prompt: str, system: str = "", max_tokens: int = 3500) -> str:
    key = st.session_state.api_key.strip()
    if not key: raise ValueError("API 키가 없습니다. 사이드바에 키를 입력해주세요.")
    messages = [{"role":"system","content":system + "\nReturn ONLY valid JSON. No markdown."}] if system else []
    messages.append({"role":"user","content":prompt})
    last_err = None
    for model in GROQ_MODELS:
        try:
            # 🌟 response_format 강제 적용으로 잘림 완벽 방지
            payload = {"model":model,"messages":messages,"max_tokens":max_tokens,"temperature":0.7,"response_format":{"type":"json_object"}}
            resp = requests.post(GROQ_URL, headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"}, json=payload, timeout=60)
        except Exception as e: last_err = Exception(f"네트워크 오류: {e}"); continue
        if resp.status_code == 401: raise Exception("API 키 오류")
        if resp.status_code == 429: last_err = Exception("한도 초과"); time.sleep(2); continue
        if not resp.ok: last_err = Exception(f"HTTP {resp.status_code}"); continue
        try:
            text = resp.json()["choices"][0]["message"]["content"]
            if text: return text
        except: last_err = Exception("응답 파싱 실패"); continue
    raise last_err or Exception("모든 모델 실패")

def gen_concept(seed: dict) -> dict:
    prompt = f"""한국 교육 랜딩페이지 UI 디자이너.
무드: "{seed['mood']}" | 레이아웃: {seed.get("layout","auto")} | 폰트: {seed.get("font","auto")}
규칙: extraCSS는 문자열 내에 반드시 작은따옴표(')만 사용. 최소 150자 이상 작성.
다음 JSON 구조를 반드시 지켜서 반환할 것:
{{"name":"컨셉명(한글)","dark":true,"heroStyle":"immersive","c1":"#hex","c2":"#hex","c3":"#hex","c4":"#hex","bg":"#hex","bg2":"#hex","bg3":"#hex","textHex":"#hex","textRgb":"r,g,b","bdAlpha":"rgba(r,g,b,.12)","displayFont":"Google Font","bodyFont":"Noto Sans KR","fontWeights":"400;700;900","displayFontWeights":"400;700","borderRadiusPx":8,"btnBorderRadiusPx":100,"particle":"none","ctaGradient":"linear-gradient(135deg,#hex,#hex)","extraCSS":"..."}}"""
    res = safe_json(call_ai(prompt, max_tokens=3000))
    if seed.get("particle_hint"): res["particle"] = seed["particle_hint"]
    return res

def gen_copy(ctx: str, ptype: str, tgt: str, plabel: str) -> dict:
    schemas = {
        "신규 커리큘럼": '{"bannerSub":"","bannerTitle":"","bannerLead":"","ctaCopy":"","ctaTitle":"","ctaSub":"","ctaBadge":"","statBadges":[],"introTitle":"","introDesc":"","introBio":"","introBadges":[],"whyTitle":"","whySub":"","whyReasons":[["이모지","제목","설명"],["이모지","제목","설명"],["이모지","제목","설명"]],"curriculumTitle":"","curriculumSub":"","curriculumSteps":[["01","이름","설명","기간"],["02","이름","설명","기간"],["03","이름","설명","기간"],["04","이름","설명","기간"]],"targetTitle":"","targetItems":["","","",""],"reviews":[["인용문","이름","뱃지"],["인용문","이름","뱃지"],["인용문","이름","뱃지"]],"faqs":[["질문","답변"],["질문","답변"]]}',
        "이벤트": '{"bannerSub":"","bannerTitle":"","bannerLead":"","ctaCopy":"","ctaTitle":"","ctaSub":"","ctaBadge":"","statBadges":[],"eventTitle":"","eventDesc":"","eventDetails":[["이모지","라벨","값"],["이모지","라벨","값"]],"benefitsTitle":"","eventBenefits":[{"icon":"이모지","title":"혜택명","desc":"설명","badge":"뱃지","no":"01"},{"icon":"이모지","title":"혜택명","desc":"설명","badge":"뱃지","no":"02"}],"deadlineTitle":"","deadlineMsg":"","reviews":[["인용문","이름","뱃지"]]}',
        "기획전": '{"festHeroTitle":"","festHeroCopy":"","festHeroSub":"","festHeroStats":[["수치","라벨"]],"festLineupTitle":"","festLineupSub":"","festLineup":[{"name":"강사명","tag":"분야","tagline":"소개","badge":"뱃지","emoji":"이모지"}],"festBenefitsTitle":"","festBenefits":[{"icon":"이모지","title":"명","desc":"설명","badge":"뱃지","no":"01"}],"festCtaTitle":"","festCtaSub":""}',
    }
    prompt = f"""한국 최고 수능 교육 랜딩페이지 카피라이터.
맥락: "{ctx}" | 목적: {ptype} | 대상: {tgt} | 브랜드: {plabel}
한자 금지. JSON만 반환: {schemas.get(ptype, schemas['신규 커리큘럼'])}"""
    return safe_json(call_ai(prompt, max_tokens=3500))

# ── CSS 및 빌더 ──
BASE_CSS = """*,*::before,*::after{box-sizing:border-box;margin:0;padding:0} html{scroll-behavior:smooth} body{font-family:var(--fb);background:var(--bg);color:var(--text);overflow-x:hidden;-webkit-font-smoothing:antialiased} a{text-decoration:none;color:inherit} .rv{opacity:0;transform:translateY(18px);transition:opacity .85s cubic-bezier(.16,1,.3,1),transform .85s cubic-bezier(.16,1,.3,1)} .rv.on{opacity:1;transform:none} @keyframes up{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}} .btn-p{display:inline-flex;align-items:center;gap:7px;background:var(--c1);color:#fff;font-family:var(--fb);font-size:14px;font-weight:700;padding:13px 30px;border-radius:var(--r-btn,100px);border:none;cursor:pointer;box-shadow:0 4px 18px rgba(0,0,0,.18);text-decoration:none} .sec{padding:clamp(52px,7vw,80px) clamp(24px,6vw,70px)} .sec.alt{background:var(--bg2)} .tag-line{display:inline-flex;align-items:center;gap:8px;font-size:9.5px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--c1);margin-bottom:13px} .tag-line::before{content:'';display:block;width:20px;height:1px;background:var(--c1)} .sec-h2{font-family:var(--fh);font-size:clamp(24px,3.8vw,36px);font-weight:700;line-height:1.2;letter-spacing:-.03em;color:var(--text);margin-bottom:11px} .sec-sub{font-size:14px;line-height:1.95;color:var(--t70);margin-bottom:36px;max-width:540px} .card{background:var(--bg);border:1px solid var(--bd);border-radius:var(--r,12px);padding:22px}"""

def _bg(bg_url, dark):
    if not bg_url: return {"hero_bg":"background:var(--bg)","overlay":"","tc":"color:var(--text)","t70c":"color:var(--t70)","c1c":"var(--c1)","bdc":"var(--bd)","card_bg":"rgba(255,255,255,.05)" if dark else "var(--bg)","btn_s":"","top_brd":"var(--bd)","blur":"","shadow":""}
    # 🌟 그림자 200% 강화
    return {"hero_bg":f"background:var(--bg) url('{bg_url}') center/cover no-repeat","overlay":'<div style="position:absolute;inset:0;background:rgba(0,0,0,0.7);z-index:1;pointer-events:none"></div>',"tc":"color:#fff","t70c":"color:rgba(255,255,255,.9)","c1c":"#fff","bdc":"rgba(255,255,255,.3)","card_bg":"rgba(0,0,0,.65)","btn_s":"color:#fff;border-color:rgba(255,255,255,.6)","top_brd":"rgba(255,255,255,.2)","blur":"backdrop-filter:blur(12px);","shadow":"text-shadow:0 4px 16px rgba(0,0,0,0.9);"}

def sec_banner(d, cp, T):
    title, lead, cta = strip_hanja(cp.get("bannerTitle",d["purpose_label"])), strip_hanja(cp.get("bannerLead",f"{d['target']} 커리큘럼")), strip_hanja(cp.get("ctaCopy","수강신청"))
    bg_url = st.session_state.get("uploaded_bg_b64") or cp.get("bg_photo_url", "")
    s = _bg(bg_url, T["dark"])
    return f'<section id="hero" style="position:relative;min-height:95vh;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;overflow:hidden;{s["hero_bg"]}">{s["overlay"]}<div style="position:relative;z-index:2;max-width:860px;padding:40px"><h1 style="font-family:var(--fh);font-size:clamp(48px,8vw,100px);font-weight:900;line-height:1.1;letter-spacing:-.05em;{s["tc"]};{s["shadow"]}" class="st">{title}</h1><p style="font-size:clamp(15px,1.8vw,18px);line-height:1.8;{s["t70c"]};margin:24px 0;{s["shadow"]}">{lead}</p><a class="btn-p" href="#" style="box-shadow:0 6px 20px rgba(0,0,0,.5);font-size:16px;padding:16px 42px">{cta} →</a></div></section>'

def sec_intro(d, cp, T): return f'<section class="sec alt" id="intro"><div class="rv"><div class="tag-line">소개</div><h2 class="sec-h2 st">{cp.get("introTitle","강사 소개")}</h2><p class="sec-sub">{cp.get("introDesc","수능의 본질을 꿰뚫습니다.")}</p></div></section>'
def sec_why(d, cp, T): return f'<section class="sec" id="why"><div class="rv"><div class="tag-line">이유</div><h2 class="sec-h2 st">{cp.get("whyTitle","이 강의가 필요한 이유")}</h2></div></section>'
def sec_curriculum(d, cp, T): return f'<section class="sec alt" id="curriculum"><div class="rv"><div class="tag-line">커리큘럼</div><h2 class="sec-h2 st">{cp.get("curriculumTitle","커리큘럼")}</h2></div></section>'
def sec_target(d, cp, T): return f'<section class="sec" id="target"><div class="rv"><div class="tag-line">대상</div><h2 class="sec-h2 st">{cp.get("targetTitle","이런 분들께 추천합니다")}</h2></div></section>'
def sec_reviews(d, cp, T): return f'<section class="sec alt" id="reviews"><div class="rv"><div class="tag-line">수강평</div><h2 class="sec-h2 st">생생한 수강평</h2></div></section>'
def sec_faq(d, cp, T): return f'<section class="sec" id="faq"><div class="rv"><div class="tag-line">FAQ</div><h2 class="sec-h2 st">자주 묻는 질문</h2></div></section>'
def sec_cta(d, cp, T): return f'<section style="padding:100px 40px;text-align:center;background:{T["cta"]}"><h2 style="font-family:var(--fh);font-size:40px;color:#fff;font-weight:900">{cp.get("ctaTitle","지금 시작하세요")}</h2></section>'

def build_html(secs: list) -> str:
    T = get_theme()
    cp = dict(st.session_state.custom_copy or {})
    if st.session_state.get("uploaded_bg_b64"): cp["bg_photo_url"] = st.session_state.uploaded_bg_b64
    elif st.session_state.bg_photo_url: cp["bg_photo_url"] = st.session_state.bg_photo_url
    d = {"name":st.session_state.instructor_name,"subject":st.session_state.subject,"purpose_label":st.session_state.purpose_label,"target":st.session_state.target}
    mp = {"banner":sec_banner,"intro":sec_intro,"why":sec_why,"curriculum":sec_curriculum,"target":sec_target,"reviews":sec_reviews,"faq":sec_faq,"cta":sec_cta}
    body = "\n".join(mp[s](d,cp,T) for s in secs if s in mp)
    return f'<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"/><link href="{T["fonts"]}" rel="stylesheet"/><style>:root{{{T["vars"]}}}{BASE_CSS}{T["extra_css"]}</style></head><body>{body}<script>const ro=new IntersectionObserver(es=>{{es.forEach(e=>{{if(e.isIntersecting){{e.target.classList.add("on");ro.unobserve(e.target);}}}});}},{{threshold:.06}});document.querySelectorAll(".rv").forEach(el=>ro.observe(el));</script></body></html>'

# ── 사이드바 UI ──
st.markdown("""<style>[data-testid="stSidebar"]{background:#08090F;border-right:1px solid #1A1F2E;} [data-testid="stSidebar"] label,[data-testid="stSidebar"] p{color:#A0AABB!important;font-size:12px!important;} .stButton>button{border-radius:8px!important;font-weight:700!important;border:1px solid #2A3450!important;background:#111828!important;color:#9AAAC8!important;font-size:12px!important;} .stButton>button[kind="primary"]{background:linear-gradient(135deg,#FF6B35,#E84393)!important;color:#fff!important;border:none!important;}</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🎓 강사 페이지 빌더 Pro")
    st.session_state.api_key = st.text_input("🔑 GROQ API KEY", type="password", value=st.session_state.api_key)
    
    pt = st.radio("목적", list(PURPOSE_SECTIONS.keys()), index=list(PURPOSE_SECTIONS.keys()).index(st.session_state.purpose_type))
    if pt != st.session_state.purpose_type:
        st.session_state.purpose_type = pt
        st.session_state.active_sections = PURPOSE_SECTIONS[pt].copy()
        st.rerun()

    if st.button("🎲 AI 랜덤 생성", type="primary", use_container_width=True):
        if st.session_state.api_key:
            seed = random.choice([{"mood":"사이버펑크 네온사인 다크 도시","layout":"brutalist","font":"display"},{"mood":"축구공이 돋보이는 축구장 잔디밭","layout":"immersive","font":"display"},{"mood":"야구장 밤 조명 전광판","layout":"immersive","font":"display"}])
            with st.spinner("생성 중..."):
                r = gen_concept(seed)
                st.session_state.custom_theme = r
                st.session_state.concept = "custom"
                st.session_state.bg_photo_url = build_bg_url(seed["mood"])
                st.session_state.uploaded_bg_b64 = ""
                st.rerun()

    mood_in = st.text_area("직접 묘사:", value=st.session_state.ai_mood)
    st.session_state.ai_mood = mood_in
    if st.button("✦ 이 무드로 생성", use_container_width=True):
        if mood_in.strip() and st.session_state.api_key:
            with st.spinner("생성 중..."):
                r = gen_concept({"mood":mood_in.strip(),"layout":"auto","font":"auto"})
                st.session_state.custom_theme = r
                st.session_state.concept = "custom"
                st.session_state.bg_photo_url = build_bg_url(mood_in.strip())
                st.session_state.uploaded_bg_b64 = ""
                st.rerun()

    st.markdown("**🖼 배경 이미지 직접 업로드**")
    uploaded_img = st.file_uploader("배경 이미지", type=["jpg","jpeg","png","webp"], label_visibility="collapsed")
    if uploaded_img is not None:
        try:
            # 🌟 이미지 자동 압축 로직 (6.5MB 등 뻗음 방지)
            img = Image.open(uploaded_img)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            img.thumbnail((1280, 720), Image.Resampling.LANCZOS)
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=75)
            b64 = base64.b64encode(buffered.getvalue()).decode()
            st.session_state.uploaded_bg_b64 = f"data:image/jpeg;base64,{b64}"
            st.session_state.bg_photo_url = ""
            st.success("✓ 이미지 최적화 및 적용 완료!")
        except Exception as e: st.error(f"처리 오류: {e}")
    if st.session_state.uploaded_bg_b64:
        if st.button("🗑 업로드 이미지 제거", use_container_width=True):
            st.session_state.uploaded_bg_b64 = ""
            st.rerun()

# ── 메인 화면 ──
ordered = [s for s in PURPOSE_SECTIONS[st.session_state.purpose_type] if s in st.session_state.active_sections]
final_html = build_html(ordered)

L, R = st.columns([1, 2], gap="large")
with L:
    st.markdown("### ✍️ AI 문구 생성")
    ctx = st.text_area("페이지 맥락", height=100)
    if st.button("✦ 문구 생성", type="primary", use_container_width=True) and st.session_state.api_key:
        with st.spinner("생성 중..."):
            st.session_state.custom_copy = gen_copy(ctx, st.session_state.purpose_type, st.session_state.target, st.session_state.purpose_label)
            st.rerun()
with R:
    st.markdown("### 👁 실시간 미리보기")
    import streamlit.components.v1 as components
    components.html(final_html, height=900, scrolling=True)
