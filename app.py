"""
강사 페이지 빌더 Pro v8 — MASTER REDESIGN
- 15개 파격 테마 & 고급 레이아웃 랜덤 로테이션 시스템
- Gemini 1.5 Flash 통합 및 이모지 완전 차단 엔진
- UI 가독성 및 팝업 버그 완벽 해결
"""
import streamlit as st
import requests
import json, re, time, random, unicodedata, base64

st.set_page_config(page_title="강사 페이지 빌더 Pro", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

# ══════════════════════════════════════════════════════
# SESSION STATE 초기화
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
    "uploaded_bg_b64": "", "pixabay_key": "", "bg_cache": {}, "preview_key": 0,
    "copy_tone": "✨ 압도적·카리스마", "history": [],
    "course_info": "", "textbook_info": "", "course_copy": None, "textbook_copy": None,
}
for _k, _v in _D.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

if not st.session_state.api_key:
    try:
        st.session_state.api_key = st.secrets.get("GEMINI_API_KEY", "")
        if not st.session_state.pixabay_key:
            st.session_state.pixabay_key = st.secrets.get("PIXABAY_API_KEY", "")
    except Exception:
        pass

# ══════════════════════════════════════════════════════
# 상수 & 카피라이팅 페르소나
# ══════════════════════════════════════════════════════
COPY_TONES = {
    "✨ 압도적·카리스마": "어조: 절대적인 확신과 카리스마. 수험생의 현실 안일함을 차가운 팩트로 찌름. 문장은 짧고 압도적이어야 함.",
    "🤝 철학적·감동": "어조: 선배 같은 따뜻함과 깊은 철학. 학생의 본질적인 고민을 어루만지고 감동을 주는 방식. 상황 묘사보다 감정적 울림 중심.",
    "💎 프리미엄·신뢰": "어조: 고급 브랜드처럼 절제된 톤. 수식어를 최소화하고 오직 압도적인 결과와 사실로 승부.",
    "😎 힙·MZ": "어조: 트렌디하고 감각적. 설명하지 않고 결과와 팩트만으로 쿨하게 던질 것.",
    "📖 논리적·분석": "어조: 전문적이고 데이터 중심. 출제 패턴, 숫자, 논리적 근거로 차분하게 설득.",
    "🔥 독설·팩폭": "어조: 피도 눈물도 없는 차가운 독설. 감정적 위로 절대 금지. 차가운 논리로 정신 차리게 함.",
    "🔮 광기·구원": "어조: 학생을 홀리는 듯한 극단적이고 맹신적인 문체. 오직 이 강의만이 유일한 구원이라는 오만함과 확신."
}

COPY_VARIATION_SEEDS = [
    {"style": "대비형", "bannerTitle_hint": "현재의 잘못된 공부법을 직접 저격", "lead_hint": "문제점 지적 후 유일한 해결책 제시", "why_hint": "기존 방식의 실패 원인 → 이 강의의 해결책 대비", "cta_hint": "지금 당장 바꾸지 않으면 생기는 손실 강조"},
    {"style": "감성공감형", "bannerTitle_hint": "수험생이 느끼는 본질적 외로움과 한계를 건드림", "lead_hint": "정확한 감정 상태 묘사 후 구원의 손길 제시", "why_hint": "선배의 경험담처럼 '저도 그 느낌 압니다'식 서술", "cta_hint": "망설이는 수험생의 등을 밀어주는 따뜻한 한 문장"},
    {"style": "데이터·증거형", "bannerTitle_hint": "압도적인 숫자를 전면에 배치 (예: 6개월, 1등급)", "lead_hint": "다른 강의와 본질적으로 다른 '방법론적 증거' 1문장", "why_hint": "기출 데이터와 출제 원리 등 반박 불가능한 근거로 작성", "cta_hint": "결과가 보장된 선택임을 강조하는 이성적 문장"},
    {"style": "도발·직설형", "bannerTitle_hint": "아직도 감으로 푸냐는 식의 뼈를 때리는 공격적 제목", "lead_hint": "듣기 불편하지만 부정할 수 없는 현실을 쉼표 없이 빠르게 타격", "why_hint": "학생의 핑계를 예상하고 정면으로 반박하는 구조", "cta_hint": "더 이상 속지 말고 진짜 공부를 시작하라는 직설적 명령"}
]

def get_copy_variation() -> str:
    v = random.choice(COPY_VARIATION_SEEDS)
    return (f"\n\n===이번 생성의 문구 스타일 지침 [{v['style']}]===\n"
            f"- bannerTitle 방향: {v['bannerTitle_hint']}\n"
            f"- bannerLead/introDesc 방향: {v['lead_hint']}\n"
            f"- whyReasons 방향: {v['why_hint']}\n"
            f"- ctaSub/ctaTitle 방향: {v['cta_hint']}\n"
            f"※ 위 스타일을 반드시 반영해 완전히 다른 관점의 문구를 창조할 것.")

THEMES = {
    "cinematic": {"label":"🎬 시네마틱","dark":True,"fonts":"https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;500&display=swap","vars":"--c1:#FF1744;--c2:#FF5252;--c3:#4A0010;--c4:#050005;--bg:#050005;--bg2:#0A000A;--bg3:#150010;--text:#F8F0F0;--t70:rgba(248,240,240,.7);--t45:rgba(248,240,240,.45);--bd:rgba(255,23,68,.2);--fh:'Bebas Neue','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:0px;--r-btn:2px;","extra_css":".st{letter-spacing:.08em} section.alt{background:var(--bg2)}","cta":"linear-gradient(135deg,#1A0005,#FF1744 55%,#FF5252)","heroStyle":"cinematic","particle":"embers"},
    "brutal": {"label":"◼️ 브루탈 모노","dark":False,"fonts":"https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Noto+Sans+KR:wght@400;700;900&display=swap","vars":"--c1:#1A1A1A;--c2:#444444;--c3:#E0E0E0;--c4:#000000;--bg:#F5F5F0;--bg2:#EBEBEB;--bg3:#E0E0E0;--text:#0A0A0A;--t70:rgba(10,10,10,.7);--t45:rgba(10,10,10,.45);--bd:rgba(10,10,10,.15);--fh:'Space Grotesk','Noto Sans KR',sans-serif;--fb:'Space Grotesk','Noto Sans KR',sans-serif;--r:0px;--r-btn:0px;","extra_css":".card{border:2px solid #0A0A0A!important;box-shadow:4px 4px 0 #0A0A0A!important} .btn-p{border:2px solid #fff!important;box-shadow:3px 3px 0 #fff!important} section.alt{background:var(--bg2)}","cta":"linear-gradient(135deg,#0A0A0A,#333333)","heroStyle":"billboard","particle":"none"},
    "acid": {"label":"⚡ 에시드 그린","dark":True,"fonts":"https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Noto+Sans+KR:wght@400;700;900&display=swap","vars":"--c1:#AAFF00;--c2:#CCFF44;--c3:#224400;--c4:#030703;--bg:#030703;--bg2:#060E06;--bg3:#0A1A0A;--text:#F0FFF0;--t70:rgba(240,255,240,.7);--t45:rgba(240,255,240,.45);--bd:rgba(170,255,0,.18);--on-c1:#030703;--fh:'Space Grotesk','Noto Sans KR',sans-serif;--fb:'Space Grotesk','Noto Sans KR',sans-serif;--r:0px;--r-btn:0px;","extra_css":".st{letter-spacing:.02em} .card{border-color:rgba(170,255,0,.15)!important} .btn-p{color:#030703!important}","cta":"linear-gradient(135deg,#7CFC00,#AAFF00)","heroStyle":"typographic","particle":"none"},
    "luxury": {"label":"✨ 골드 럭셔리","dark":True,"fonts":"https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,500;0,600;1,300;1,500&family=Noto+Serif+KR:wght@300;400;600&family=DM+Sans:wght@300;400;500&display=swap","vars":"--c1:#C8975A;--c2:#D4AF72;--c3:#EDD8A4;--c4:#0C0B09;--bg:#0C0B09;--bg2:#131108;--bg3:#1A1810;--text:#F5F0E8;--t70:rgba(245,240,232,.7);--t45:rgba(245,240,232,.45);--bd:rgba(200,151,90,.15);--fh:'Cormorant Garamond','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:2px;--r-btn:2px;","extra_css":".st{font-weight:300;font-style:italic}","cta":"linear-gradient(135deg,#0C0B09,#2A2010)","heroStyle":"editorial_bold"},
    "floral": {"label":"🌸 플로럴 에디토리얼","dark":False,"fonts":"https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,600;0,700;1,300;1,600&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;500&display=swap","vars":"--c1:#E8386D;--c2:#F472A8;--c3:#FFD6E7;--c4:#1A0510;--bg:#FFFAF8;--bg2:#FFF0F4;--bg3:#FFE4EE;--text:#1A0510;--t70:rgba(26,5,16,.7);--t45:rgba(26,5,16,.45);--bd:rgba(232,56,109,.12);--fh:'Cormorant Garamond','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:0px;--r-btn:100px;","extra_css":".st{font-style:italic;font-weight:700}","cta":"linear-gradient(135deg,#1A0510,#E8386D)","heroStyle":"editorial_bold","particle":"petals"},
    "cosmos": {"label":"🌌 코스모스","dark":True,"fonts":"https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Noto+Sans+KR:wght@300;400;700&family=DM+Sans:wght@300;400;500&display=swap","vars":"--c1:#7C3AED;--c2:#06B6D4;--c3:#A78BFA;--c4:#030712;--bg:#030712;--bg2:#080C18;--bg3:#0D1220;--text:#F1F5F9;--t70:rgba(241,245,249,.7);--t45:rgba(241,245,249,.45);--bd:rgba(124,58,237,.22);--fh:'Orbitron','Noto Sans KR',sans-serif;--fb:'DM Sans','Noto Sans KR',sans-serif;--r:0px;--r-btn:0px;","extra_css":".st{letter-spacing:.1em;text-transform:uppercase}","cta":"linear-gradient(135deg,#030712,#2D1B69)","heroStyle":"typographic","particle":"stars"},
}

PURPOSE_SECTIONS = {
    "신규 커리큘럼": ["banner","intro","video","grade_stats","before_after","instructor_philosophy","method","why","curriculum","course_intro","textbook_sale","target","package","reviews","faq","cta"],
    "이벤트":        ["banner","event_overview","event_benefits","event_deadline","reviews","cta"],
    "기획전":        ["fest_hero","fest_lineup","fest_benefits","fest_cta"],
}
SEC_LABELS = {
    "banner":"🏠 메인 배너","intro":"📖 강좌 핵심 소개","why":"💡 수강 이유",
    "curriculum":"📚 커리큘럼","target":"🎯 수강 대상","reviews":"⭐ 수강평",
    "faq":"❓ FAQ","cta":"📣 수강신청",
    "video":"🎬 영상 미리보기","before_after":"🔄 수강 전/후","method":"🧪 학습법 시각화","package":"📦 구성 안내",
    "grade_stats":"📊 등급 변화 성과","event_overview":"📅 이벤트 개요","event_benefits":"🎁 이벤트 혜택",
    "event_deadline":"⏰ 마감 안내","fest_hero":"🏆 기획전 히어로","fest_lineup":"👥 강사 라인업",
    "fest_benefits":"🎁 기획전 혜택","fest_cta":"📣 기획전 CTA","custom_section":"✏️ 기타 섹션",
    "course_intro": "📖 강좌 소개","textbook_sale": "📦 교재 판매","instructor_philosophy": "💭 강사 철학",
}

# ══════════════════════════════════════════════════════
# 유틸 & AI 연동 (Google Gemini 1.5 Flash 통합)
# ══════════════════════════════════════════════════════
def strip_hanja(text: str) -> str:
    if not isinstance(text, str): return str(text) if text is not None else ""
    result = []
    for ch in text:
        cp = ord(ch)
        if 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF: continue
        result.append(ch)
    return "".join(result).strip()

def clean_obj(obj):
    if isinstance(obj, str): return strip_hanja(obj)
    if isinstance(obj, dict): return {k: clean_obj(v) for k,v in obj.items()}
    if isinstance(obj, list): return [clean_obj(i) for i in obj]
    return obj

def safe_json(raw: str) -> dict:
    start = raw.find('{')
    if start == -1: raise ValueError("JSON parsing failed")
    depth, in_string, escape, end = 0, False, False, -1
    for i in range(start, len(raw)):
        c = raw[i]
        if escape: escape = False; continue
        if c == '\\': escape = True; continue
        if c == '"': in_string = not in_string; continue
        if not in_string:
            if c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0: end = i; break
    if end == -1: raise ValueError("JSON incomplete")
    s = raw[start:end+1].replace('\n', ' ').replace('\r', ' ')
    s = re.sub(r",\s*}", "}", s)
    s = re.sub(r",\s*]", "]", s)
    try: return clean_obj(json.loads(s))
    except Exception as e: raise ValueError(f"JSON Error: {e}")

def call_ai(prompt: str, system: str = "", max_tokens: int = 2500) -> str:
    key = st.session_state.api_key.strip()
    if not key: raise ValueError("API 키가 없습니다. 사이드바에서 Gemini API 키를 입력해주세요.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    full_prompt = f"{system}\n\n{prompt}\n\n[중요] 반드시 JSON 형식으로만 답변하세요. 마크다운이나 추가 설명은 절대 금지합니다."
    data = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {
            "temperature": 1.15, # 🌟 창의성 극대화 🌟
            "maxOutputTokens": max_tokens,
            "responseMimeType": "application/json"
        }
    }
    last_err = None
    for attempt in range(3): # 에러 시 3번 재시도하는 안전장치
        try:
            resp = requests.post(url, headers={"Content-Type": "application/json"}, json=data, timeout=60)
            if resp.status_code == 429:
                last_err = Exception("⏳ 무료 요청 횟수 초과. 10초 후 재시도...")
                time.sleep(10); continue
            if not resp.ok:
                err_msg = resp.json().get("error", {}).get("message", resp.text[:150])
                last_err = Exception(f"API 오류 ({resp.status_code}): {err_msg}")
                time.sleep(2); continue
            text = resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if text and text.strip(): return text
        except requests.exceptions.RequestException as e:
            last_err = Exception(f"네트워크 오류: {e}"); time.sleep(3)
    raise last_err or Exception("AI 생성 실패. 잠시 후 시도해주세요.")

def fetch_pixabay_url(query: str) -> str:
    key = st.session_state.get("pixabay_key", "").strip()
    if not key: return ""
    if query in st.session_state.bg_cache: return st.session_state.bg_cache[query]
    try:
        r = requests.get("https://pixabay.com/api/", params={"key": key, "q": query, "image_type": "photo", "orientation": "horizontal", "per_page": 20, "safesearch": "true", "min_width": 1280, "order": "popular"}, timeout=8)
        if r.ok and r.json().get("hits"):
            hit = random.choice(r.json()["hits"][:10])
            url = hit.get("largeImageURL") or hit.get("webformatURL", "")
            if url: st.session_state.bg_cache[query] = url; return url
    except: pass
    return ""

def _get_instructor_context() -> str:
    ip, name, subj = st.session_state.get("inst_profile") or {}, st.session_state.instructor_name, st.session_state.subject
    if not ip.get("found") or not name: return f"강사명: {name} | 과목: {subj}" if name else f"과목: {subj}"
    return "\n".join([f"강사: {name} ({subj})", f"이력: {ip.get('bio','')}", f"슬로건: '{ip.get('slogan','')}'", f"고유 학습법: {', '.join(ip.get('signatureMethods',[]))}"])

def gen_theme_declaration(ctx: str, ptype: str) -> dict:
    prompt = f"""수능 교육 랜딩페이지 방향성 설계.
맥락: "{ctx}", 목적: {ptype}
JSON 반환: {{"declaration": "이 페이지 전체 방향 선언문 (2-3문장)","core_keyword": "핵심 키워드 단어 1개"}}"""
    try: return safe_json(call_ai(prompt, max_tokens=500))
    except: return {"declaration": ctx, "core_keyword": "수능"}

def gen_copy(ctx: str, ptype: str, tgt: str, plabel: str) -> dict:
    inst_ctx, variation_hint = _get_instructor_context(), get_copy_variation()
    theme_decl = gen_theme_declaration(ctx, ptype)
    st.session_state["_theme_declaration"] = theme_decl

    # 🌟 이모지 완전 삭제 & 메인 제목 짧게 제한 🌟
    schemas = {
        "신규 커리큘럼": '{"bannerSub":"과목 본질을 찌르는 15자 이내","bannerTitle":"단 3~4어절의 파격적이고 짧은 제목 (예: 1등급의 공식, 절대 길게 쓰지 마세요)","brandTagline":"영문 슬로건 한 문장","bannerLead":"뻔한 위로가 아닌 현 상황을 찌르는 팩트폭력 리드문 (길게)","bannerTags":["키워드1","키워드2"],"ctaCopy":"수강신청","ctaTitle":"강력한 CTA 제목","ctaSub":"지금 안 하면 손해라는 서브 문구","ctaBadge":"10자이내","introTitle":"강사의 절대적 권위 제목","introDesc":"왜 이 강의를 들어야만 하는지 날카롭게 서술 (길게)","introBio":"시그니처 1문장","whyTitle":"파격적 제목","whySub":"30자이내","whyReasons":[["01","직설적인 짧은 제목","학생이 읽고 아차 싶을 만큼 뼈 때리는 구체적 이유와 해결책 서술 (최소 80자 이상)"],["02","제목","서술"],["03","제목","서술"]],"curriculumTitle":"20자이내","curriculumSub":"30자이내","curriculumSteps":[["01","단계명","이 시기에 학생들이 하는 착각과 이 단계가 그걸 어떻게 부수는지 서술","기간"],["02","단계","서술","기간"],["03","단계","서술","기간"],["04","단계","서술","기간"]],"targetTitle":"이런 학생이라면 반드시 들어라","targetItems":["구체적인 절망적 상황 묘사 1","상황 묘사 2","상황 묘사 3","상황 묘사 4"],"reviews":[["진짜 학생이 흥분해서 쓴 것 같은 매우 길고 구체적인 후기","이름","변화뱃지"],["후기","이름","뱃지"],["후기","이름","뱃지"]],"faqs":[["질문","답변"]],"videoTitle":"영상 제목","videoSub":"설명","videoTag":"OFFICIAL TRAILER"}',
        "이벤트": '{"bannerSub":"10자","bannerTitle":"단 3~4어절의 파격적인 이벤트 제목 (10자 이내 엄수)","brandTagline":"이벤트 분위기 한 문장","bannerLead":"참여하지 않으면 손해라는 긴박감 리드","bannerTags":["이벤트특징1","이벤트특징2"],"ctaCopy":"행동 유도","ctaTitle":"CTA","ctaSub":"서브문구","ctaBadge":"15자","eventTitle":"20자","eventDesc":"50자이상","eventDetails":[["일정","날짜"],["대상","값"],["혜택","값"]],"benefitsTitle":"20자","eventBenefits":[{"no":"01","title":"혜택명","desc":"50자이상","badge":"8자"},{"no":"02","title":"혜택명","desc":"50자","badge":"8자"}],"deadlineTitle":"20자","deadlineMsg":"70자 긴박감"}',
        "기획전": '{"festHeroTitle":"단 3~4어절의 강렬한 기획전 제목 (10자 이내 엄수)","festHeroCopy":"30자","festHeroSub":"50자이상","brandTagline":"분위기 문장","festHeroStats":[["수치","라벨"],["수치","라벨"]],"festLineupTitle":"20자","festLineupSub":"40자","festLineup":[{"name":"강사명","tag":"분야","tagline":"40자","badge":"뱃지"},{"name":"강사명","tag":"분야","tagline":"40자","badge":"뱃지"}],"festBenefitsTitle":"20자","festBenefits":[{"no":"01","title":"혜택명","desc":"50자이상","badge":"8자"},{"no":"02","title":"혜택명","desc":"50자","badge":"8자"}],"festCtaTitle":"CTA제목","festCtaSub":"50자이상"}'
    }

    prompt = f"""당신은 Apple과 메가스터디의 최고급 런칭 페이지 카피라이터입니다.
단순히 정보를 나열하지 말고, 압도적인 카리스마와 깊은 철학이 느껴지는 최고급 카피를 창조하세요.

===문구 생성 지침===
{variation_hint}
# 방향성: {theme_decl.get('declaration', '')}
# 핵심 키워드: [{theme_decl.get('core_keyword', '')}]
# 절대 금지어: 이모지(절대 쓰지 말 것!), 최고의, 체계적인, 합리적인, 실력 향상, 교수

===강사 정보===
{inst_ctx}
목적: {ptype} | 카피 어조: {COPY_TONES.get(st.session_state.copy_tone, "")}

===문구 품질 기준===
1. 제목(Title)은 무조건 3~4어절 이내로 짧고 강렬하게 끊어치세요.
2. 설명(Desc/Lead)은 길이 제한 없이, 학생의 고통을 직설적으로 찌르고 서사적으로 길게 쓰세요.
3. 이모지(😊, 🎯 등)는 절대로 쓰지 마세요. 오직 텍스트의 무게감으로 승부하세요.
4. 숫자를 활용하여 프리미엄 신뢰감을 주세요.

JSON만 반환 (마크다운 금지):
{schemas.get(ptype, schemas['신규 커리큘럼'])}"""
    return safe_json(call_ai(prompt, max_tokens=3500))

def gen_section(sec_id: str) -> dict:
    inst_ctx, ptype = _get_instructor_context(), st.session_state.purpose_type
    theme_decl = st.session_state.get("_theme_declaration", {})
    variation_hint = get_copy_variation()

    schemas = {
        "banner": '{"bannerSub":"15자이내","bannerTitle":"단 3~4어절의 아주 짧은 제목 (절대 길게 쓰지 마세요)","brandTagline":"영문 슬로건","bannerLead":"뻔한 위로가 아닌 현 상황 팩트폭력 (길게)","bannerTags":["키워드1","키워드2"],"ctaCopy":"10자","statBadges":[]}',
        "why":    '{"whyTitle":"20자","whySub":"30자","whyReasons":[["01","직설적인 짧은 제목","학생 입장에서 구체적 설명 최소 80자"],["02","12자","80자"],["03","12자","80자"]]}',
        "curriculum": '{"curriculumTitle":"20자","curriculumSub":"30자","curriculumSteps":[["01","8자","이 단계 통해 무엇이 달라지는지 50자 이상 설명","기간"],["02","8자","50자 이상","기간"],["03","8자","50자 이상","기간"],["04","8자","50자 이상","기간"]]}',
        "reviews": '{"reviews":[["지금도 쓸 것 같은 생생한 50-70자 인용문, 구체적 점수·방법 언급","이름","뱃지"],["50-70자 인용문","이름","뱃지"],["50-70자 인용문","이름","뱃지"]]}',
    }
    schema = schemas.get(sec_id, '{"title":"제목","desc":"설명"}')
    sec_name = SEC_LABELS.get(sec_id, sec_id)

    prompt = f"""당신은 업계 최고 수준의 브랜드 마케터입니다. "{sec_name}" 섹션만 새롭게 생성하세요.
{variation_hint}
{inst_ctx}
목적: {ptype} | 카피 어조: {COPY_TONES.get(st.session_state.copy_tone, "")}

=== 🚨 극단적 다양성 및 이모지 금지 규칙 🚨 ===
1. 흔하고 뻔한 이모지는 절대로 쓰지 마세요. 텍스트로만 승부하세요.
2. 재생성할 때마다 완전히 새로운 관점과 문장 구조를 시도하세요.
3. 배너/섹션 제목은 무조건 짧게! 설명은 길고 직설적으로.

JSON만 반환. 마크다운 금지:
{schema}"""
    return safe_json(call_ai(prompt, max_tokens=1500))

# ══════════════════════════════════════════════════════
# HTML/CSS 엔진
# ══════════════════════════════════════════════════════
def get_theme() -> dict:
    t = THEMES.get(st.session_state.concept, THEMES["brutal"])
    return {"fonts":t["fonts"],"vars":t["vars"],"extra_css":t.get("extra_css",""),"dark":t.get("dark",True),"cta":t.get("cta","var(--c1)")}

BASE_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0} html{scroll-behavior:smooth}
body{font-family:var(--fb);background:var(--bg);color:var(--text);overflow-x:hidden;-webkit-font-smoothing:antialiased}
h1,h2,h3,p,span,div{word-break:keep-all;overflow-wrap:break-word;white-space:normal}
a{text-decoration:none;color:inherit} .card *,.rv *{overflow:visible;min-width:0}
.rv{opacity:0;transform:translateY(32px) scale(.98);transition:all .8s cubic-bezier(.16,1,.3,1)}
.rv.on{opacity:1;transform:translateY(0) scale(1)}
.marquee-container {width:100vw;max-width:100%;overflow-x:hidden;position:absolute;top:50%;transform:translateY(-50%) rotate(-3deg);white-space:nowrap;z-index:0;pointer-events:none;}
.marquee-content {display:inline-block;font-family:'Black Han Sans',var(--fh);font-size:clamp(80px,12vw,200px);font-weight:900;color:var(--c1);opacity:0.05;line-height:1;text-transform:uppercase;animation:marquee 20s linear infinite;}
@keyframes marquee {0%{transform:translateX(0);}100%{transform:translateX(-50%);}}
"""

# ══════════════════════════════════════════════════════
# 섹션 빌더 (파격 레이아웃 랜덤 변화)
# ══════════════════════════════════════════════════════
def sec_banner(d, cp, T):
    sub = strip_hanja(cp.get("bannerSub", d["subject"]+" 완성"))
    title = strip_hanja(cp.get("bannerTitle", d["purpose_label"]))
    lead = strip_hanja(cp.get("bannerLead", f"{d['target']}을 위한 커리큘럼"))
    cta = strip_hanja(cp.get("ctaCopy", "수강신청"))
    bg_url = cp.get("bg_photo_url", "")
    dark = T["dark"]

    # 🌟 재생성 시마다 레이아웃이 랜덤으로 변함 (preview_key 활용) 🌟
    v = ((sum(ord(c) for c in title + lead) + st.session_state.get('preview_key', 0)) % 3) + 1

    if v == 1: # 거대 타이포 마키 (Brutal)
        bg_text = f"{title} " * 5
        text_col = "#fff" if (dark or bg_url) else "var(--text)"
        bg_style = f"background: url('{bg_url}') center/cover no-repeat;" if bg_url else "background: var(--bg3);"
        overlay = '<div style="position:absolute;inset:0;background:rgba(0,0,0,0.6);z-index:1;"></div>' if bg_url else ''
        return (f'<section id="hero" style="position:relative; min-height:100vh; overflow:hidden; {bg_style}; display:flex; flex-direction:column; justify-content:center; text-align:center;">'
                + overlay + f'<div class="marquee-container"><div class="marquee-content">{bg_text}{bg_text}</div></div>'
                f'<div style="position:relative; z-index:2; padding:0 20px; max-width:1200px; margin:0 auto;">'
                f'<div style="display:inline-block; font-size:12px; font-weight:800; letter-spacing:0.2em; color:var(--c1); border:2px solid var(--c1); padding:8px 24px; border-radius:50px; margin-bottom:30px;">{sub}</div>'
                f'<h1 style="font-family:\'Black Han Sans\', var(--fh); font-size:clamp(60px, 8vw, 150px); font-weight:900; line-height:1.05; letter-spacing:-0.05em; color:{text_col}; margin-bottom:30px;">{title}</h1>'
                f'<p style="font-size:clamp(16px, 2vw, 22px); line-height:1.8; color:rgba(255,255,255,0.8) if {dark} else var(--t70); max-width:800px; margin:0 auto 50px; font-weight:600;">{lead}</p>'
                f'<a href="#cta" style="display:inline-block; background:var(--c1); color:var(--bg); padding:20px 50px; font-size:18px; font-weight:900; font-family:var(--fh); box-shadow: 10px 10px 0px rgba(0,0,0,0.3); transition:transform 0.2s;">{cta} →</a>'
                f'</div></section>')
    
    elif v == 2: # 애플 스타일 (Clean)
        bg_style = f"background: url('{bg_url}') center/cover no-repeat;" if bg_url else "background: linear-gradient(180deg, var(--bg) 0%, var(--bg2) 100%);"
        overlay = '<div style="position:absolute;inset:0;background:rgba(0,0,0,0.5);z-index:1;"></div>' if bg_url else ''
        text_col = "#fff" if (dark or bg_url) else "var(--text)"
        return (f'<section id="hero" style="position:relative; min-height:90vh; display:flex; align-items:center; justify-content:center; text-align:center; overflow:hidden; {bg_style}">'
                + overlay + f'<div class="rv" style="position:relative; z-index:2; max-width:1200px; padding: 20px;">'
                f'<h3 style="font-family:var(--fh); font-size:clamp(14px, 2vw, 20px); font-weight:800; color:var(--c1); letter-spacing:0.3em; margin-bottom:30px;">{sub}</h3>'
                f'<h1 style="font-family:var(--fh); font-size:clamp(50px, 9vw, 140px); font-weight:900; color:{text_col}; line-height:1.05; letter-spacing:-0.05em; margin-bottom:40px;">{title}</h1>'
                f'<p style="font-size:clamp(16px, 2.2vw, 26px); color:rgba(255,255,255,0.7) if {dark} else var(--t70); font-weight:500; line-height:1.7; max-width:800px; margin:0 auto 60px;">{lead}</p>'
                f'<a href="#cta" style="display:inline-block; background:var(--c1); color:var(--bg); padding:20px 60px; border-radius:50px; font-size:clamp(16px, 2vw, 20px); font-weight:900; font-family:var(--fh); box-shadow: 0 10px 30px rgba(0,0,0,0.3);">{cta}</a>'
                f'</div></section>')
    else: # 좌우 분할 매거진
        bg_style = f"background: url('{bg_url}') center/cover no-repeat;" if bg_url else "background: var(--bg2);"
        overlay = '<div style="position:absolute;inset:0;background:rgba(0,0,0,0.7);z-index:1;"></div>' if bg_url else ''
        text_col = "#fff" if (dark or bg_url) else "var(--text)"
        return (f'<section id="hero" style="position:relative; min-height:90vh; display:flex; align-items:center; overflow:hidden; {bg_style}">'
                + overlay + f'<div class="rv" style="position:relative; z-index:2; padding: 100px clamp(20px, 5vw, 80px); width:100%; max-width:1400px; margin:0 auto; text-align:left;">'
                f'<div style="display:inline-block; font-size:14px; font-weight:800; color:var(--bg); background:var(--c1); padding:6px 16px; margin-bottom:24px;">{sub}</div>'
                f'<h1 style="font-family:var(--fh); font-size:clamp(45px, 7vw, 110px); font-weight:900; color:{text_col}; line-height:1.1; letter-spacing:-0.03em; margin-bottom:30px;">{title}</h1>'
                f'<div style="width:60px; height:4px; background:var(--c1); margin-bottom:30px;"></div>'
                f'<p style="font-size:clamp(15px, 1.8vw, 22px); color:rgba(255,255,255,0.7) if {dark} else var(--t70); font-weight:500; line-height:1.8; max-width:600px; margin-bottom:50px;">{lead}</p>'
                f'<a href="#cta" style="display:inline-block; background:transparent; border:2px solid var(--c1); color:{text_col}; padding:16px 40px; font-size:16px; font-weight:800; transition: all 0.2s;" onmouseover="this.style.background=\'var(--c1)\'; this.style.color=\'var(--bg)\'" onmouseout="this.style.background=\'transparent\'; this.style.color=\'{text_col}\'">{cta} →</a>'
                f'</div></section>')

def sec_why(d, cp, T):
    t = strip_hanja(cp.get('whyTitle', '이 강의가 필요한 이유'))
    s = strip_hanja(cp.get('whySub', f"{d['subject']} 1등급의 비결"))
    reasons = cp.get('whyReasons', [])
    safe_r = [(str(it[0]), str(it[1]), str(it[2])) for it in reasons if isinstance(it, list) and len(it) >= 3]

    # 🌟 재생성 시마다 레이아웃이 랜덤으로 변함 (preview_key 활용) 🌟
    v = ((sum(ord(c) for c in t + s) + st.session_state.get('preview_key', 0)) % 3) + 1

    if v == 1: # 거대 숫자 + 비대칭 겹침 (Brutal)
        bg_text = f"{t} " * 10
        rh = ""
        for i, (no, tt, dc) in enumerate(safe_r):
            align = "flex-start" if i % 2 == 0 else "flex-end"
            mt = "margin-top: -30px;" if i > 0 else "" 
            rh += (f'<div class="rv d{min(i+1,4)}" style="align-self:{align}; {mt} width: clamp(300px, 85%, 750px); position:relative; z-index:{i+2};">'
                   f'<div style="position:absolute; top:-70px; left:-30px; font-family:var(--fh); font-size: clamp(150px, 18vw, 250px); font-weight:900; color:var(--c1); opacity:0.08; line-height:1; pointer-events:none; z-index:-1;">{no}</div>'
                   f'<div style="background:var(--bg3); padding:50px 60px; border-top: 4px solid var(--c1); box-shadow: 20px 20px 0px rgba(0,0,0,0.2);">'
                   f'<div style="font-family:var(--fh); font-size: 16px; color:var(--c1); letter-spacing:0.2em; font-weight:800; margin-bottom:16px;">POINT {no}</div>'
                   f'<div style="font-family:var(--fh); font-size: clamp(28px, 3.5vw, 42px); font-weight:900; color:var(--text); margin-bottom:24px; line-height:1.2;">{strip_hanja(tt)}</div>'
                   f'<p style="font-size: clamp(16px, 1.8vw, 20px); line-height:1.9; color:var(--t70); margin:0; font-weight:500;">{strip_hanja(dc)}</p>'
                   f'</div></div>')
        return (f'<section class="sec" id="why" style="position:relative; overflow:hidden; padding: 180px 20px;"><div class="marquee-container"><div class="marquee-content">{bg_text}{bg_text}</div></div>'
                f'<div style="max-width:1100px; margin:0 auto; position:relative; z-index:2;"><div class="rv" style="margin-bottom:120px; text-align:center;">'
                f'<div style="color:var(--c1); font-weight:800; letter-spacing:0.3em; font-size:14px;">WHY CHOOSE US</div>'
                f'<h2 style="font-family:\'Black Han Sans\',var(--fh); font-size:clamp(40px, 6vw, 80px); font-weight:900; color:var(--text); letter-spacing:-0.05em; margin-top:20px;">{t}</h2>'
                f'<p style="margin: 24px auto 0; font-size:20px; color:var(--c1); font-weight:700;">{s}</p></div><div style="display:flex; flex-direction:column; gap:60px;">{rh}</div></div></section>')

    elif v == 2: # 애플 스타일 세로 정렬
        rh = "".join(f'<div class="rv" style="display:flex; gap:40px; align-items:flex-start; padding:50px 0; border-bottom:1px solid var(--bd);"><div style="font-family:var(--fh); font-size:60px; font-weight:900; color:var(--c1); line-height:1;">{no}.</div><div><h3 style="font-family:var(--fh); font-size:clamp(26px, 3.5vw, 40px); font-weight:900; color:var(--text); margin-bottom:20px;">{strip_hanja(tt)}</h3><p style="font-size:clamp(16px, 1.8vw, 20px); color:var(--t70); line-height:1.85; margin:0; font-weight:500;">{strip_hanja(dc)}</p></div></div>' for no, tt, dc in safe_r)
        return (f'<section class="sec alt" id="why" style="padding: 160px 20px;"><div style="max-width:900px; margin:0 auto;"><div class="rv" style="text-align:left; margin-bottom:80px;">'
                f'<div style="font-size:13px; color:var(--c1); font-weight:800;">{s}</div><h2 style="font-family:var(--fh); font-size:clamp(45px, 6vw, 75px); font-weight:900; color:var(--text); margin-top:16px;">{t}</h2>'
                f'</div><div style="border-top:2px solid var(--c1);">{rh}</div></div></section>')

    else: # 프리미엄 3열 그리드
        rh = "".join(f'<div class="rv" style="padding:40px; border:1px solid var(--bd);"><div style="width:40px; height:4px; background:var(--c1); margin-bottom:30px;"></div><div style="font-family:var(--fh); font-size:14px; font-weight:800; color:var(--c1); margin-bottom:16px; letter-spacing:0.1em;">REASON {no}</div><h3 style="font-family:var(--fh); font-size:clamp(22px, 2.5vw, 28px); font-weight:900; color:var(--text); margin-bottom:24px; line-height:1.4;">{strip_hanja(tt)}</h3><p style="font-size:16px; color:var(--t70); line-height:1.8; margin:0;">{strip_hanja(dc)}</p></div>' for no, tt, dc in safe_r)
        return (f'<section class="sec" id="why" style="padding: 160px 20px; background:var(--bg2);"><div style="max-width:1200px; margin:0 auto;"><div class="rv" style="display:flex; flex-direction:column; align-items:center; text-align:center; margin-bottom:80px;">'
                f'<div style="margin-bottom:20px; color:var(--c1); font-weight:800; letter-spacing:0.2em;">WHY THIS CLASS</div><h2 style="font-family:var(--fh); font-size:clamp(36px, 5vw, 64px); font-weight:900; color:var(--text);">{t}</h2><p style="font-size:18px; color:var(--t70); margin-top:20px;">{s}</p>'
                f'</div><div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:30px;">{rh}</div></div></section>')

def sec_curriculum(d, cp, T):
    t = strip_hanja(cp.get("curriculumTitle", f"{d['purpose_label']} 커리큘럼"))
    s = strip_hanja(cp.get("curriculumSub", "단계별 완성 로드맵"))
    steps = cp.get("curriculumSteps", [])
    
    # 🌟 재생성 시마다 레이아웃 랜덤 변화 🌟
    v = ((sum(ord(c) for c in t + s) + st.session_state.get('preview_key', 0)) % 3) + 1
    sh = ""

    if v == 1:
        for idx, step in enumerate(steps):
            sh += f'<div class="rv" style="display:flex;gap:20px;align-items:flex-start;padding:20px 0;border-bottom:1px solid var(--bd)"><div style="flex-shrink:0;width:40px;height:40px;border-radius:4px;background:var(--c1);display:flex;align-items:center;justify-content:center;font-family:var(--fh);font-size:16px;color:var(--bg);font-weight:900">✓</div><div style="flex:1"><div style="display:flex;align-items:center;gap:10px;margin-bottom:6px"><span style="font-family:var(--fh);font-size:18px;font-weight:800;color:var(--text)">{strip_hanja(str(step[1]))}</span></div><p style="font-size:14px;line-height:1.8;color:var(--t70);margin:0">{strip_hanja(str(step[2]))}</p></div></div>'
        return f'<section class="sec alt" id="curriculum"><div style="max-width:900px;margin:0 auto"><div class="rv" style="margin-bottom:40px"><h2 style="font-family:var(--fh); font-size:clamp(36px, 5vw, 64px); font-weight:900; color:var(--text);">{t}</h2><p>{s}</p></div>{sh}</div></section>'
    else:
        for idx, step in enumerate(steps):
            sh += f'<div class="rv" style="padding:32px;border:1px solid var(--bd);background:var(--bg3);"><div style="font-family:var(--fh);font-size:32px;font-weight:900;color:var(--c1);margin-bottom:10px;">{step[0]}</div><div style="font-family:var(--fh);font-size:20px;font-weight:700;color:var(--text);margin-bottom:10px">{strip_hanja(str(step[1]))}</div><p style="font-size:14px;line-height:1.85;color:var(--t70);margin:0">{strip_hanja(str(step[2]))}</p></div>'
        return f'<section class="sec" id="curriculum"><div style="max-width:1200px;margin:0 auto"><div class="rv" style="text-align:center;margin-bottom:48px"><h2 style="font-family:var(--fh); font-size:clamp(36px, 5vw, 64px); font-weight:900; color:var(--text);">{t}</h2><p>{s}</p></div><div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(250px, 1fr));gap:20px;">{sh}</div></div></section>'

# 기타 남은 간단한 섹션들
def sec_intro(d, cp, T): return f'<section class="sec" id="intro"><div style="max-width:900px;margin:0 auto;text-align:center;"><h2 style="font-family:var(--fh);font-size:clamp(28px,4vw,52px);font-weight:900;color:var(--text);margin-bottom:20px;">"{strip_hanja(cp.get("introTitle", ""))}"</h2><p style="font-size:18px;line-height:2;color:var(--t70);">{strip_hanja(cp.get("introDesc", ""))}</p></div></section>'
def sec_cta(d, cp, T): return f'<section style="padding:100px 20px;text-align:center;background:{T["cta"]}"><h2 style="font-family:var(--fh);font-size:clamp(32px,5.5vw,64px);font-weight:900;color:#fff;margin-bottom:16px">{strip_hanja(cp.get("ctaTitle", ""))}</h2><p style="color:rgba(255,255,255,0.8);font-size:18px;margin-bottom:40px;">{strip_hanja(cp.get("ctaSub", ""))}</p><a href="#" style="background:#fff;color:#000;padding:20px 60px;font-size:18px;font-weight:900;border-radius:50px;text-decoration:none;">{strip_hanja(cp.get("ctaCopy", "신청하기"))}</a></section>'
def sec_reviews(d, cp, T): return f'<section class="sec alt" id="reviews"><div style="max-width:1000px;margin:0 auto;text-align:center;"><h2 style="font-family:var(--fh);font-size:clamp(36px,5vw,64px);font-weight:900;color:var(--text);">생생한 수강생 후기</h2><p style="color:var(--t70);margin-bottom:60px;">결과로 증명합니다.</p></div></section>'

# ══════════════════════════════════════════════════════
# HTML 빌더
# ══════════════════════════════════════════════════════
def build_html(secs: list) -> str:
    T = get_theme()
    cp = dict(st.session_state.custom_copy or {})
    if st.session_state.bg_photo_url: cp["bg_photo_url"] = st.session_state.bg_photo_url
    d = {"name":st.session_state.instructor_name, "subject":st.session_state.subject, "purpose_label":st.session_state.purpose_label, "target":st.session_state.target}
    
    mp = {"banner":sec_banner, "intro":sec_intro, "why":sec_why, "curriculum":sec_curriculum, "cta":sec_cta, "reviews":sec_reviews}
    sections_html = [mp[s](d, cp, T) for s in secs if s in mp]
    
    return f'<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><link href="https://fonts.googleapis.com/css2?family=Black+Han+Sans&display=swap" rel="stylesheet"/><link href="{T["fonts"]}" rel="stylesheet"/><style>:root{{{T["vars"]}}}{BASE_CSS}</style></head><body>{"".join(sections_html)}</body></html>'

# ══════════════════════════════════════════════════════
# UI CSS (사이드바 + 메인)
# ══════════════════════════════════════════════════════
st.markdown("""<style>
[data-testid="stSidebar"] {background:#07080F; border-right:1px solid #161A28;}
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] .stCaption {color:#8A9AB8 !important; font-size:12px !important;}
[data-testid="stSidebar"] h3 {color:#E0E8F8 !important; font-size:16px !important; font-weight:800 !important;}

/* 🌟 입력창 글씨 및 드롭다운 팝업 완벽 해결 🌟 */
[data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea, [data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background-color: #1A2038 !important; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; border: 1px solid #343C58 !important; border-radius: 6px !important;
}
div[data-baseweb="popover"], div[data-baseweb="popover"] > div, div[data-baseweb="popover"] ul {background-color: #1A2038 !important; border-color: #343C58 !important;}
div[data-baseweb="popover"] li {color: #FFFFFF !important; font-size: 13px !important; background: transparent !important;}
div[data-baseweb="popover"] li:hover, div[data-baseweb="popover"] li[aria-selected="true"] {background-color: #FF6B35 !important; color: #FFFFFF !important;}

span[data-baseweb="tag"] {background-color: #232A40 !important; color: #FFFFFF !important; border: 1px solid #343C58 !important; border-radius: 6px !important; padding: 4px 10px !important;}
.stButton>button {border-radius:6px !important; font-weight:700 !important; border:1px solid #232A40 !important; background:#0D1220 !important; color:#8A9AB8 !important;}
.stButton>button:hover {background:#161E38 !important; color:#C0CDE8 !important;}
.stButton>button[kind="primary"] {background:linear-gradient(135deg,#FF6B35,#E84393) !important; color:#fff !important; border:none !important;}
.sec-hdr {font-size:9.5px; font-weight:800; letter-spacing:.14em; color:#3A4868; padding:10px 0;}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="sec-hdr">🔑 GOOGLE GEMINI API KEY</div>', unsafe_allow_html=True)
    api_in = st.text_input("API Key", type="password", value=st.session_state.api_key, placeholder="AI Studio 키 입력", label_visibility="collapsed")
    if api_in != st.session_state.api_key: st.session_state.api_key = api_in
    if st.session_state.api_key: st.success("✓ Gemini API 연결 완료!", icon="✅")
    else: st.markdown('<a href="https://aistudio.google.com/app/apikey" target="_blank" style="font-size:11px;color:#5A6A8A">👆 구글 AI 스튜디오 → API key 발급받기</a>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="sec-hdr">🎨 테마 선택</div>', unsafe_allow_html=True)
    cols_n = st.columns(2)
    themes_list = ["cinematic", "brutal", "acid", "luxury", "floral", "cosmos"]
    for i, k in enumerate(themes_list):
        with cols_n[i % 2]:
            if st.button(THEMES[k]["label"], key=f"th_{k}", type="primary" if st.session_state.concept == k else "secondary", use_container_width=True):
                st.session_state.concept = k; st.session_state.preview_key += 1; st.rerun()

    st.markdown("---")
    st.markdown('<div class="sec-hdr">🎭 카피 어조 (AI 페르소나)</div>', unsafe_allow_html=True)
    tone_options = list(COPY_TONES.keys())
    if st.session_state.copy_tone not in tone_options: st.session_state.copy_tone = tone_options[0]
    selected_tone = st.selectbox("어조", tone_options, index=tone_options.index(st.session_state.copy_tone), label_visibility="collapsed")
    if selected_tone != st.session_state.copy_tone: st.session_state.copy_tone = selected_tone; st.rerun()

    st.markdown("---")
    st.markdown('<div class="sec-hdr">📑 섹션 ON/OFF</div>', unsafe_allow_html=True)
    st.session_state.active_sections = st.multiselect("표시할 섹션 순서", options=list(SEC_LABELS.keys()), default=["banner","why","curriculum","cta"], format_func=lambda x: SEC_LABELS.get(x, x))

# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════
L, R = st.columns([1, 3], gap="large")

with L:
    st.markdown("### ✍️ AI 문구 생성")
    ctx = st.text_area("페이지 맥락 입력", height=100, placeholder="예: 2026 수능 영어 파이널. 선티 선생님.")
    if st.button("✦ 전체 문구 AI 생성", type="primary", use_container_width=True):
        if not st.session_state.api_key: st.warning("API 키를 입력해주세요.")
        else:
            with st.spinner("최고급 카피 작성 중..."):
                try:
                    r = gen_copy(ctx, st.session_state.purpose_type, st.session_state.target, st.session_state.purpose_label)
                    st.session_state.custom_copy = r
                    st.session_state.preview_key += 1
                    st.success("✓ 카피 생성 완료!")
                    st.rerun()
                except Exception as e: st.error(f"실패: {e}")

    st.markdown("### 🎲 개별 섹션 재생성")
    regen_secs = [s for s in st.session_state.active_sections if s in SEC_LABELS]
    for row_start in range(0, len(regen_secs), 3):
        cols_r = st.columns(3)
        for i, sid in enumerate(regen_secs[row_start:row_start+3]):
            with cols_r[i]:
                if st.button(f"↺ {SEC_LABELS[sid].split(' ')[1]}", key=f"regen_{sid}", use_container_width=True):
                    with st.spinner("재생성 중..."):
                        try:
                            if not st.session_state.custom_copy: st.session_state.custom_copy = {}
                            st.session_state.custom_copy.update(gen_section(sid))
                            st.session_state.preview_key += 1
                            st.rerun()
                        except Exception as e: st.error(f"실패: {e}")

with R:
    st.markdown("### 👁 실시간 미리보기")
    st.info("💡 오른쪽 '↺ 개별 섹션 재생성' 버튼을 누를 때마다 디자인 레이아웃과 문구가 3가지 스타일로 파격 변신합니다!")
    final_html = build_html([s for s in st.session_state.active_sections])
    import streamlit.components.v1 as components
    components.html(final_html, height=1200, scrolling=True)
