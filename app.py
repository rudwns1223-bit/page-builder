import streamlit as st
import google.generativeai as genai
import json
import re
import time
import requests
import random

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="강사 페이지 빌더 Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# THEMES
# ─────────────────────────────────────────────
THEMES = {
    "sakura": {
        "label": "🌸 벚꽃 봄", "dark": False,
        "fonts": "https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;700&display=swap",
        "vars": "--c1:#B5304A;--c2:#E89BB5;--c3:#F5CEDA;--c4:#2A111A;--bg:#FBF6F4;--bg2:#F7EFF1;--bg3:#F2E5E9;--text:#2A111A;--t70:rgba(42,17,26,.7);--t45:rgba(42,17,26,.45);--bd:rgba(42,17,26,.10);--fh:'Playfair Display','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:12px;--r-btn:100px;",
        "extra_css": ".st{font-style:italic}", "variant": "editorial",
    },
    "fire": {
        "label": "🔥 다크 파이어", "dark": True,
        "fonts": "https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@400;700;900&family=DM+Sans:wght@300;400;700&display=swap",
        "vars": "--c1:#FF4500;--c2:#FF8C00;--c3:#FFD700;--c4:#0D0705;--bg:#0D0705;--bg2:#130A04;--bg3:#1A0E06;--text:#F1F5F9;--t70:rgba(241,245,249,.7);--t45:rgba(241,245,249,.45);--bd:rgba(255,69,0,.22);--fh:'Bebas Neue','Noto Sans KR',sans-serif;--fb:'DM Sans','Noto Sans KR',sans-serif;--r:4px;--r-btn:4px;",
        "extra_css": ".st{letter-spacing:.05em;text-shadow:0 0 20px rgba(255,69,0,.35)}", "variant": "dark",
    },
    "ocean": {
        "label": "🌊 오션 블루", "dark": False,
        "fonts": "https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap",
        "vars": "--c1:#0EA5E9;--c2:#38BDF8;--c3:#BAE6FD;--c4:#0C4A6E;--bg:#F0F9FF;--bg2:#E0F2FE;--bg3:#BAE6FD;--text:#0C1A2E;--t70:rgba(12,26,46,.7);--t45:rgba(12,26,46,.45);--bd:rgba(14,165,233,.15);--fh:'Syne','Noto Sans KR',sans-serif;--fb:'Noto Sans KR',sans-serif;--r:10px;--r-btn:100px;",
        "extra_css": ".st{font-weight:800}", "variant": "modern",
    },
    "luxury": {
        "label": "✨ 골드 럭셔리", "dark": True,
        "fonts": "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,500;0,600;1,300;1,500&family=Noto+Serif+KR:wght@300;400;600&family=DM+Sans:wght@300;400;500&display=swap",
        "vars": "--c1:#C8975A;--c2:#D4AF72;--c3:#EDD8A4;--c4:#0C0B09;--bg:#0C0B09;--bg2:#131108;--bg3:#1A1810;--text:#F5F0E8;--t70:rgba(245,240,232,.7);--t45:rgba(245,240,232,.45);--bd:rgba(200,151,90,.15);--fh:'Cormorant Garamond','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:2px;--r-btn:2px;",
        "extra_css": ".st{font-weight:300;font-style:italic}", "variant": "editorial",
    },
    "eco": {
        "label": "🌿 에코 그린", "dark": False,
        "fonts": "https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;500;700&display=swap",
        "vars": "--c1:#059669;--c2:#34D399;--c3:#A7F3D0;--c4:#064E3B;--bg:#F0FDF4;--bg2:#DCFCE7;--bg3:#BBF7D0;--text:#064E3B;--t70:rgba(6,78,59,.7);--t45:rgba(6,78,59,.45);--bd:rgba(5,150,105,.15);--fh:'DM Serif Display','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:14px;--r-btn:100px;",
        "extra_css": ".st{font-style:italic}", "variant": "organic",
    },
    "winter": {
        "label": "❄️ 윈터 스노우", "dark": False,
        "fonts": "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,600;0,700;0,800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap",
        "vars": "--c1:#1E40AF;--c2:#3B82F6;--c3:#BFDBFE;--c4:#0F172A;--bg:#F8FAFF;--bg2:#EFF6FF;--bg3:#DBEAFE;--text:#0F172A;--t70:rgba(15,23,42,.7);--t45:rgba(15,23,42,.45);--bd:rgba(30,64,175,.12);--fh:'Plus Jakarta Sans','Noto Sans KR',sans-serif;--fb:'Plus Jakarta Sans','Noto Sans KR',sans-serif;--r:8px;--r-btn:100px;",
        "extra_css": ".st{font-weight:800}", "variant": "modern",
    },
    "cosmos": {
        "label": "🌌 코스모스", "dark": True,
        "fonts": "https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Noto+Sans+KR:wght@300;400;700&family=DM+Sans:wght@300;400;500&display=swap",
        "vars": "--c1:#7C3AED;--c2:#06B6D4;--c3:#A78BFA;--c4:#030712;--bg:#030712;--bg2:#080C18;--bg3:#0D1220;--text:#F1F5F9;--t70:rgba(241,245,249,.7);--t45:rgba(241,245,249,.45);--bd:rgba(124,58,237,.22);--fh:'Orbitron','Noto Sans KR',sans-serif;--fb:'DM Sans','Noto Sans KR',sans-serif;--r:0px;--r-btn:0px;",
        "extra_css": ".st{letter-spacing:.12em;text-transform:uppercase}", "variant": "dark",
    },
}

SUBJECT_KW = {
    "영어": ["빈칸 추론", "EBS 연계", "순서·삽입", "어법·어휘"],
    "수학": ["수1·수2", "미적분", "확률과 통계", "킬러 문항"],
    "국어": ["독해력", "문학", "비문학", "화법과 작문"],
    "사회": ["생활과 윤리", "한국지리", "세계사", "경제"],
    "과학": ["물리학", "화학", "생명과학", "지구과학"],
}

RANDOM_MOODS = [
    "사이버펑크 보라 네온사인, 비오는 다크 도시",
    "고대 이집트 황금 신전, 사막 모래와 오벨리스크",
    "북유럽 스칸디나비아 미니멀, 하얀 안개 자작나무 숲",
    "수험생 새벽 4시 형광등 책상, 집중과 고요",
    "극지방 오로라 청록 보라 새벽하늘",
    "빈티지 옥스퍼드 도서관, 가죽 책 양피지",
    "다크 아카데미아 빅토리안 고딕 도서관",
    "오래된 수학 교실 분필 칠판 먼지 냄새",
    "겨울 새벽 눈 덮인 사찰 고요 집중 먹빛",
    "여름 밤 루프탑 바, 도시 스카이라인 인디고",
    "그리스 지중해 흰 건물 코발트 블루 바다",
    "가을 단풍 교정 은행나무, 따뜻한 주황 갈색",
    "네온 팝아트 비비드 원색 90s 리트로",
    "미래 우주선 내부 홀로그램 테크 UI",
    "흑백 필름 사진관, 빈티지 모노크롬",
]

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "api_key": "",
        "concept": "sakura",
        "custom_theme": None,
        "instructor_name": "",
        "subject": "영어",
        "purpose": "2026 수능 파이널 완성",
        "target": "고3·N수",
        "custom_copy": None,
        "generated_html": "",
        "ai_mood_input": "",
        "status_msg": "",
        "instructor_profile": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─────────────────────────────────────────────
# AI HELPERS
# ─────────────────────────────────────────────
def call_gemini(prompt: str, system: str = "", json_mode: bool = True, max_tokens: int = 3000) -> str:
    api_key = st.session_state.api_key.strip()
    if not api_key:
        raise ValueError("API 키가 없습니다. 사이드바에서 입력해주세요.")

    genai.configure(api_key=api_key)

    models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b"]
    last_err = None

    for model_name in models_to_try:
        try:
            cfg = genai.GenerationConfig(max_output_tokens=max_tokens)
            if json_mode:
                cfg = genai.GenerationConfig(
                    max_output_tokens=max_tokens,
                    response_mime_type="application/json",
                )
            sys_parts = (system or "Return only valid JSON.") + ("\n\nReturn strictly valid JSON only. Do not wrap in markdown." if json_mode else "")
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=cfg,
                system_instruction=sys_parts,
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            last_err = e
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
                time.sleep(1.5)
                continue
            if "400" in err_str:
                continue
            raise
    raise last_err or Exception("Gemini 모든 모델 실패")


def safe_json(raw: str) -> dict:
    s = raw.strip()
    s = re.sub(r"```json\s*", "", s)
    s = re.sub(r"```\s*", "", s)
    s = s.strip()
    first = s.find("{")
    last = s.rfind("}")
    if first > 0:
        s = s[first:]
    if last >= 0 and last < len(s) - 1:
        s = s[:last + 1]
    try:
        return json.loads(s)
    except Exception:
        pass
    # Second attempt: fix common issues
    s2 = re.sub(r'(?<!\\)"((?:[^"\\]|\\.)*)"', lambda m: '"' + m.group(1).replace("\n", " ") + '"', s)
    try:
        return json.loads(s2)
    except Exception as e:
        raise ValueError(f"JSON 파싱 실패: {e}\n원본: {raw[:300]}")


# ─────────────────────────────────────────────
# AI GENERATION FUNCTIONS
# ─────────────────────────────────────────────
def gen_concept(mood: str) -> dict:
    prompt = f"""당신은 한국 교육 랜딩페이지 UI/UX 디자이너입니다.
다음 무드로 CSS 테마를 생성하세요: "{mood}"

규칙:
- extraCSS 안의 CSS 문자열은 반드시 작은따옴표(') 사용
- 모든 값은 한 줄로 (줄바꿈 없음)
- particle: "petals"는 벚꽃/봄 무드만, "embers"=불꽃, "snow"=겨울, "stars"=우주, "gold"=황금, "leaves"=자연, 나머지="none"

다음 JSON만 반환:
{{
  "name":"컨셉이름(2-4한글+이모지)",
  "dark":true,
  "c1":"#hex",
  "c2":"#hex",
  "c3":"#hex",
  "c4":"#hex",
  "bg":"#hex",
  "bg2":"#hex",
  "bg3":"#hex",
  "textHex":"#hex",
  "textRgb":"r,g,b",
  "bdAlpha":"rgba(r,g,b,.12)",
  "displayFont":"Google Font 이름",
  "bodyFont":"Noto Sans KR",
  "fontWeights":"400;700;900",
  "displayFontWeights":"400;700",
  "borderRadiusPx":8,
  "btnBorderRadiusPx":100,
  "particle":"none",
  "heroPhotoQuery":"english photo keywords OR empty",
  "ctaGradient":"linear-gradient(135deg,#hex,#hex)",
  "extraCSS":"CSS rules using single quotes only"
}}"""
    raw = call_gemini(prompt, "Return ONLY valid compact JSON. extraCSS must use single quotes.", json_mode=True)
    return safe_json(raw)


def gen_copy(context: str, instructor_name: str, subject: str, target: str, purpose: str) -> dict:
    inst_ctx = f"강사: {instructor_name} {subject}." if instructor_name else ""
    prompt = f"""한국어 교육 마케팅 카피라이터. 다음 맥락으로 랜딩페이지 전 섹션 문구를 생성하라.

맥락: "{context}"
과목: {subject} | 대상: {target} | 목적: {purpose}
{inst_ctx}

아래 JSON만 반환 (마크다운 없이, 값에 줄바꿈 없이):
{{"bannerSub":"8자이내","bannerTitle":"15자이내","bannerLead":"40자이내","ctaCopy":"8자이내","ctaTitle":"제목<br>2줄가능","ctaSub":"25자이내","ctaBadge":"15자이내","statBadges":[["수치","라벨"],["수치","라벨"],["수치","라벨"]],"introTitle":"15자이내","introDesc":"60자이내","introBio":"40자이내","introBadges":[["수치","라벨"],["수치","라벨"],["수치","라벨"]],"whyTitle":"15자이내","whySub":"25자이내","whyReasons":[["이모지","10자","40자"],["이모지","10자","40자"],["이모지","10자","40자"]],"curriculumTitle":"20자이내","curriculumSub":"25자이내","curriculumSteps":[["01","7자","12자","기간"],["02","7자","12자","기간"],["03","7자","12자","기간"],["04","7자","12자","기간"]],"targetTitle":"15자이내","targetItems":["20자이내","항목2","항목3","항목4"],"reviews":[["인용문25자","이름","뱃지"],["인용문","이름","뱃지"],["인용문","이름","뱃지"]],"faqs":[["질문12자","답변35자"],["질문","답변"],["질문","답변"]]}}"""
    raw = call_gemini(prompt, "한국어 교육 카피라이터. 반드시 유효한 JSON만 반환.", json_mode=True, max_tokens=4000)
    return safe_json(raw)


def search_instructor(name: str, subject: str) -> dict:
    prompt = f"""Search for the Korean online educator "{name}" who teaches "{subject}" for 수능.
Return ONLY this JSON (no markdown, single-line strings):
{{"found":true,"bio":"2-3 sentences","style":"teaching style","slogan":"their motto or empty","signatureMethods":["method1"],"signatureCurriculumName":"curriculum name or empty","desc":"value proposition","badges":[["stat","label"],["stat","label"],["stat","label"]]}}"""
    raw = call_gemini(prompt, "Korean education researcher. Return ONLY valid compact JSON.", json_mode=True)
    return safe_json(raw)


# ─────────────────────────────────────────────
# HTML BUILDER
# ─────────────────────────────────────────────
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
.btn-s{display:inline-flex;align-items:center;gap:7px;background:transparent;color:var(--text);font-family:var(--fb);font-size:14px;font-weight:600;padding:12px 22px;border-radius:var(--r-btn,100px);border:1.5px solid var(--bd);cursor:pointer;transition:border-color .15s,color .15s;text-decoration:none}
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

def get_theme_data():
    if st.session_state.concept == "custom" and st.session_state.custom_theme:
        ct = st.session_state.custom_theme
        df = ct.get("displayFont", "Noto Sans KR")
        df_enc = df.replace(" ", "+")
        bf = ct.get("bodyFont", "Noto Sans KR")
        bf_enc = bf.replace(" ", "+")
        fw = ct.get("fontWeights", "400;700;900").replace(";", ";")
        dfw = ct.get("displayFontWeights", "400;700").replace(";", ";")
        fonts = f"https://fonts.googleapis.com/css2?family={df_enc}:wght@{dfw.replace(';',';')}&family={bf_enc}:wght@{fw.replace(';',';')}&display=swap"
        r = ct.get("borderRadiusPx", 8)
        rb = ct.get("btnBorderRadiusPx", 100)
        tr = ct.get("textRgb", "255,255,255")
        bd = ct.get("bdAlpha", "rgba(255,255,255,.12)")
        vars_str = (
            f"--c1:{ct['c1']};--c2:{ct['c2']};--c3:{ct['c3']};--c4:{ct['c4']};"
            f"--bg:{ct['bg']};--bg2:{ct['bg2']};--bg3:{ct['bg3']};"
            f"--text:{ct['textHex']};--t70:rgba({tr},.7);--t45:rgba({tr},.45);"
            f"--bd:{bd};--fh:'{df}','Noto Serif KR',serif;"
            f"--fb:'{bf}',sans-serif;--r:{r}px;--r-btn:{rb}px;"
        )
        return {
            "fonts": fonts,
            "vars": vars_str,
            "extra_css": ct.get("extraCSS", ""),
            "dark": ct.get("dark", True),
            "variant": "modern",
            "cta_gradient": ct.get("ctaGradient", f"linear-gradient(135deg,{ct['c4']},{ct['c1']})"),
        }
    t = THEMES.get(st.session_state.concept, THEMES["sakura"])
    cta_map = {
        "sakura": "linear-gradient(135deg,#2A111A,#B5304A)",
        "fire": "linear-gradient(135deg,#0D0705,#FF4500 60%,#FF8C00)",
        "ocean": "linear-gradient(135deg,#0C4A6E,#0EA5E9)",
        "luxury": "linear-gradient(135deg,#0C0B09,#1A1810 60%,#2A2010)",
        "eco": "linear-gradient(135deg,#064E3B,#059669)",
        "winter": "linear-gradient(135deg,#1E3A8A,#3B82F6)",
        "cosmos": "linear-gradient(135deg,#030712,#1a0a3e 50%,#2D1B69)",
    }
    return {
        "fonts": t["fonts"],
        "vars": t["vars"],
        "extra_css": t.get("extra_css", ""),
        "dark": t.get("dark", False),
        "variant": t.get("variant", "modern"),
        "cta_gradient": cta_map.get(st.session_state.concept, "linear-gradient(135deg,var(--c4),var(--c1))"),
    }


def build_html(sections: list[str]) -> str:
    T = get_theme_data()
    cp = st.session_state.custom_copy or {}
    d = {
        "name": st.session_state.instructor_name or "선생님",
        "subject": st.session_state.subject,
        "purpose": st.session_state.purpose,
        "target": st.session_state.target,
    }

    dark_card = ".card{background:var(--bg2)!important}" if T["dark"] else ""

    body_parts = []
    for sec in sections:
        if sec == "banner":
            body_parts.append(build_banner(d, cp, T))
        elif sec == "intro":
            body_parts.append(build_intro(d, cp, T))
        elif sec == "why":
            body_parts.append(build_why(d, cp, T))
        elif sec == "curriculum":
            body_parts.append(build_curriculum(d, cp, T))
        elif sec == "target":
            body_parts.append(build_target(d, cp, T))
        elif sec == "reviews":
            body_parts.append(build_reviews(d, cp, T))
        elif sec == "faq":
            body_parts.append(build_faq(d, cp, T))
        elif sec == "cta":
            body_parts.append(build_cta(d, cp, T))

    body = "\n".join(body_parts)

    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>{d['name']} {d['subject']} · {cp.get('bannerTitle', d['purpose'])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="{T['fonts']}" rel="stylesheet"/>
<style>:root{{{T['vars']}}}{BASE_CSS}{T['extra_css']}{dark_card}</style>
</head><body>
{body}
<script>
const ro=new IntersectionObserver(es=>{{es.forEach(e=>{{if(e.isIntersecting){{e.target.classList.add('on');ro.unobserve(e.target);}}}});}},{{threshold:.06}});
document.querySelectorAll('.rv').forEach(el=>ro.observe(el));
</script></body></html>"""


def build_banner(d, cp, T):
    sub = cp.get("bannerSub", d["subject"] + " 완성")
    title = cp.get("bannerTitle", d["purpose"])
    lead = cp.get("bannerLead", f"{d['target']}을 위한 최강 커리큘럼")
    cta = cp.get("ctaCopy", "수강신청하기")
    stats = cp.get("statBadges", [["98%", "수강 만족도"], ["1,200+", "합격생"], ["15년+", "강의 경력"]])
    kws = SUBJECT_KW.get(d["subject"], ["개념", "기출", "실전", "파이널"])
    stats_html = "".join(
        f'<div><div style="font-family:var(--fh);font-size:clamp(20px,3vw,28px);font-weight:900;color:var(--c1);letter-spacing:-.03em">{sv}</div>'
        f'<div style="font-size:9px;color:var(--t45);font-weight:600;letter-spacing:.1em;text-transform:uppercase;margin-top:2px">{sl}</div></div>'
        for sv, sl in stats
    )
    kw_html = "".join(
        f'<span style="font-size:9.5px;font-weight:700;padding:5px 12px;border-radius:var(--r-btn,100px);color:var(--c1);border:1px solid var(--bd)">{k}</span>'
        for k in kws
    )
    inst_line = f'<div style="display:inline-flex;align-items:center;gap:8px;margin-top:20px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:4px;padding:6px 14px"><span style="font-size:11px;color:var(--t45)">{d["name"]} 선생님</span></div>' if d["name"] and d["name"] != "선생님" else ""

    return f"""<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;background:var(--bg);display:grid;grid-template-columns:1fr 380px">
  <div style="position:relative;z-index:2;display:flex;flex-direction:column;justify-content:center;padding:clamp(60px,8vw,100px) clamp(24px,4vw,52px) clamp(60px,8vw,100px) clamp(32px,6vw,88px)">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:32px;animation:up .65s cubic-bezier(.16,1,.3,1) both">
      <div style="width:24px;height:1.5px;background:var(--c1)"></div>
      <span style="font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:var(--c1)">{sub}</span>
    </div>
    <h1 style="font-family:var(--fh);font-size:clamp(44px,6.5vw,90px);font-weight:900;line-height:.88;letter-spacing:-.05em;color:var(--text);animation:up .95s .1s cubic-bezier(.16,1,.3,1) both" class="st">{title}</h1>
    <p style="font-size:clamp(13px,1.4vw,15.5px);line-height:2.05;color:var(--t70);margin-top:24px;max-width:400px;animation:up .85s .22s cubic-bezier(.16,1,.3,1) both;padding-left:14px;border-left:2px solid var(--c2)">{lead}</p>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:20px;animation:up .8s .34s cubic-bezier(.16,1,.3,1) both">{kw_html}</div>
    {inst_line}
    <div style="display:flex;gap:12px;margin-top:30px;animation:up .8s .44s cubic-bezier(.16,1,.3,1) both"><a class="btn-p" href="#">{cta} →</a><a class="btn-s" href="#">강의 미리보기</a></div>
    <div style="display:flex;gap:28px;margin-top:52px;animation:up .75s .6s cubic-bezier(.16,1,.3,1) both">{stats_html}</div>
  </div>
  <div style="background:{'rgba(255,255,255,.03)' if T['dark'] else 'var(--bg3)'};border-left:1px solid var(--bd);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:52px 28px">
    <div style="width:100%;background:{'rgba(255,255,255,.05)' if T['dark'] else 'var(--bg)'};border:1px solid var(--bd);border-radius:var(--r,12px);overflow:hidden">
      <div style="background:var(--c1);padding:20px 24px;text-align:center">
        <div style="font-family:var(--fh);font-size:22px;font-weight:900;color:#fff">{title}</div>
      </div>
      <div style="padding:20px 24px">
        {"".join(f'<div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid var(--bd)"><span style="font-size:11px;color:var(--t45);font-weight:600">{l}</span><span style="font-size:11.5px;font-weight:700">{v}</span></div>' for l,v in [["강의 대상",d["target"]],["과목",d["subject"]],["목적",d["purpose"][:12]+"…"]])}
        <a class="btn-p" href="#" style="width:100%;justify-content:center;margin-top:16px;display:flex">{cta} →</a>
      </div>
    </div>
  </div>
</section>"""


def build_intro(d, cp, T):
    title = cp.get("introTitle", f"{d['name']} 선생님 소개")
    desc = cp.get("introDesc", f"{d['subject']} 최상위권 합격의 비결, 직접 경험하세요.")
    bio = cp.get("introBio", f"전국 {d['subject']} 강사 중 압도적 합격률 1위")
    badges = cp.get("introBadges", [["98%", "수강 만족도"], ["1,200+", "합격생 수"], ["15년+", "강의 경력"], ["#1", "과목 랭킹"]])
    badges_html = "".join(
        f'<div style="text-align:center;padding:16px;border:1px solid var(--bd);border-radius:var(--r,10px)">'
        f'<div style="font-family:var(--fh);font-size:22px;font-weight:900;color:var(--c1)">{bv}</div>'
        f'<div style="font-size:9px;color:var(--t45);font-weight:600;letter-spacing:.1em;text-transform:uppercase;margin-top:3px">{bl}</div></div>'
        for bv, bl in badges
    )
    return f"""<section class="sec alt" id="intro">
  <div class="rv"><div class="tag-line">강사 소개</div><h2 class="sec-h2 st">{title}</h2><p class="sec-sub">{desc}</p></div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px" class="rv d1">{badges_html}</div>
  <div style="margin-top:20px;padding:16px 20px;border-left:3px solid var(--c1);background:var(--bg3);border-radius:0 var(--r,8px) var(--r,8px) 0" class="rv d2">
    <p style="font-size:13px;line-height:1.9;color:var(--t70)">{bio}</p>
  </div>
</section>"""


def build_why(d, cp, T):
    title = cp.get("whyTitle", "이 강의가 필요한 이유")
    sub = cp.get("whySub", f"{d['subject']} 1등급의 비결")
    reasons = cp.get("whyReasons", [
        ["🎯", "유형별 완전 정복", f"수능 {d['subject']} 출제 유형을 완전히 분석하여 어떤 문제도 흔들리지 않는 실력을 만듭니다."],
        ["📊", "데이터 기반 학습", "10년간의 기출 데이터를 분석하여 출제 패턴을 예측하고 효율적으로 학습합니다."],
        ["⚡", "실전 속도 훈련", "정확도와 속도를 동시에 잡아 실전에서 완벽한 시간 배분이 가능하도록 훈련합니다."],
    ])
    reasons_html = "".join(
        f'<div class="card"><div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">'
        f'<div style="width:44px;height:44px;border-radius:var(--r,12px);background:var(--c1);display:flex;align-items:center;justify-content:center;font-size:20px">{icon}</div>'
        f'<div style="font-family:var(--fh);font-size:15px;font-weight:700;color:var(--text)" class="st">{ttl}</div></div>'
        f'<p style="font-size:13px;line-height:1.85;color:var(--t70)">{desc}</p></div>'
        for icon, ttl, desc in reasons
    )
    return f"""<section class="sec" id="why">
  <div class="rv"><div class="tag-line">수강 이유</div><h2 class="sec-h2 st">{title}</h2><p class="sec-sub">{sub}</p></div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px" class="rv d1">{reasons_html}</div>
</section>"""


def build_curriculum(d, cp, T):
    title = cp.get("curriculumTitle", f"{d['purpose']} 커리큘럼")
    sub = cp.get("curriculumSub", "체계적인 4단계 완성 로드맵")
    steps = cp.get("curriculumSteps", [
        ["01", "개념 완성", "핵심 개념 정리", "4주"],
        ["02", "유형 훈련", "기출 완전 분석", "4주"],
        ["03", "심화 특훈", "고난도 완전 정복", "4주"],
        ["04", "파이널", "실전 마무리", "4주"],
    ])
    steps_html = "".join(
        f'<div class="card" style="position:relative;overflow:hidden">'
        f'<div style="position:absolute;top:-12px;right:-8px;font-family:var(--fh);font-size:80px;font-weight:900;color:var(--c1);opacity:.05;line-height:1">{no}</div>'
        f'<div style="font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--c1);margin-bottom:8px">STEP {no}</div>'
        f'<div style="font-family:var(--fh);font-size:16px;font-weight:700;color:var(--text);margin-bottom:6px" class="st">{ttl}</div>'
        f'<div style="font-size:12px;color:var(--t70);margin-bottom:8px">{desc}</div>'
        f'<span style="font-size:10px;background:var(--c1);color:#fff;padding:3px 10px;border-radius:100px;font-weight:700">{dur}</span>'
        f'</div>'
        for no, ttl, desc, dur in steps
    )
    return f"""<section class="sec alt" id="curriculum">
  <div class="rv"><div class="tag-line">커리큘럼</div><h2 class="sec-h2 st">{title}</h2><p class="sec-sub">{sub}</p></div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px" class="rv d1">{steps_html}</div>
</section>"""


def build_target(d, cp, T):
    title = cp.get("targetTitle", "이런 분들께 추천합니다")
    items = cp.get("targetItems", [
        f"수능까지 {d['subject']} 점수를 확실히 올리고 싶은 분",
        "개념은 아는데 실전에서 점수가 안 나오는 분",
        "N수를 준비하며 전략적 커리큘럼이 필요한 분",
        f"{d['subject']} 상위권 도약을 위한 마지막 기회를 찾는 분",
    ])
    items_html = "".join(
        f'<div class="card" style="display:flex;align-items:center;gap:13px;padding:16px 20px">'
        f'<div style="width:26px;height:26px;min-width:26px;border-radius:50%;background:var(--c1);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;color:#fff">{i+1}</div>'
        f'<span style="font-size:14px;font-weight:500">{txt}</span></div>'
        for i, txt in enumerate(items)
    )
    return f"""<section class="sec" id="target">
  <div class="rv"><div class="tag-line">수강 대상</div><h2 class="sec-h2 st">{title}</h2></div>
  <div style="display:flex;flex-direction:column;gap:8px" class="rv d1">{items_html}</div>
</section>"""


def build_reviews(d, cp, T):
    reviews = cp.get("reviews", [
        [f'"{d["subject"]}가 이렇게 재밌는 과목이었나요? 성적도 오르고 자신감도 생겼어요!"', "고3 김OO", "1등급 달성"],
        ['"개념부터 실전까지 빈틈없는 커리큘럼. 처음부터 이 강의 들었으면 좋았을 텐데요."', "N수 이OO", "2→1등급"],
        [f'"선생님 덕분에 막연하던 {d["subject"]}의 구조가 보이기 시작했어요."', "고2 박OO", "내신 3→1등급"],
    ])
    reviews_html = "".join(
        f'<div class="card" style="display:flex;flex-direction:column;gap:10px">'
        f'<div style="color:#F59E0B;font-size:11px;margin-bottom:7px">★★★★★</div>'
        f'<p style="font-size:13px;line-height:1.85;font-weight:500">{txt}</p>'
        f'<div style="display:flex;align-items:center;justify-content:space-between;padding-top:10px;border-top:1px solid var(--bd)">'
        f'<span style="font-size:11px;color:var(--t45)">— {nm} 학생</span>'
        f'<span style="font-size:10px;background:var(--bg3);color:var(--c1);padding:3px 10px;border-radius:var(--r-btn,100px);font-weight:700;border:1px solid var(--bd)">{badge}</span>'
        f'</div></div>'
        for txt, nm, badge in reviews
    )
    return f"""<section class="sec alt" id="reviews">
  <div class="rv"><div class="tag-line">수강평</div><h2 class="sec-h2 st">생생한 수강생 후기</h2></div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px" class="rv d1">{reviews_html}</div>
</section>"""


def build_faq(d, cp, T):
    faqs = cp.get("faqs", [
        ["수강 기간은 얼마나 되나요?", "기본 수강 기간은 30일이며, 연장권 구매로 최대 90일까지 연장 가능합니다."],
        ["교재는 별도 구매인가요?", "강의 교재는 별도 구매이며, 강의 신청 페이지에서 함께 구매하실 수 있습니다."],
        ["모바일에서도 수강 가능한가요?", "PC와 모바일 모두에서 수강 가능합니다. 전용 앱을 이용하시면 더욱 편리합니다."],
    ])
    faqs_html = "".join(
        f'<div style="border:1px solid var(--bd);border-radius:var(--r,10px);overflow:hidden;margin-bottom:6px">'
        f'<div style="padding:13px 17px;background:var(--bg3);display:flex;gap:9px;align-items:flex-start">'
        f'<span style="color:var(--c1);font-weight:800;font-size:14px;flex-shrink:0">Q</span>'
        f'<span style="font-weight:600;font-size:13px">{q}</span></div>'
        f'<div style="padding:12px 17px;background:var(--bg);display:flex;gap:9px">'
        f'<span style="color:var(--t45);font-weight:700;font-size:14px;flex-shrink:0">A</span>'
        f'<span style="font-size:13px;line-height:1.75;color:var(--t70)">{a}</span></div></div>'
        for q, a in faqs
    )
    return f"""<section class="sec" id="faq">
  <div class="rv"><div class="tag-line">FAQ</div><h2 class="sec-h2 st">자주 묻는 질문</h2></div>
  <div class="rv d1">{faqs_html}</div>
</section>"""


def build_cta(d, cp, T):
    cta_title = cp.get("ctaTitle", f"지금 바로 시작해<br>{d['subject']} 1등급을 확보하세요")
    cta_sub = cp.get("ctaSub", f"{d['name']} 선생님과 함께라면 가능합니다.")
    cta_copy = cp.get("ctaCopy", "지금 수강신청하기")
    badge = cp.get("ctaBadge", f"{d['target']} 전용 · {d['purpose']}")
    return f"""<section style="padding:clamp(64px,9vw,100px) clamp(24px,6vw,72px);text-align:center;position:relative;overflow:hidden;background:{T['cta_gradient']}">
  <div style="position:absolute;top:-100px;right:-100px;width:400px;height:400px;border-radius:50%;background:rgba(255,255,255,.04);pointer-events:none"></div>
  <div style="position:relative;z-index:1">
    <div style="display:inline-block;background:rgba(255,255,255,.10);padding:5px 16px;border-radius:100px;font-size:10px;font-weight:700;color:#fff;margin-bottom:18px;letter-spacing:.06em">{badge}</div>
    <h2 style="font-family:var(--fh);font-size:clamp(26px,4.5vw,48px);font-weight:900;line-height:1.15;letter-spacing:-.03em;color:#fff;margin-bottom:12px">{cta_title}</h2>
    <p style="color:rgba(255,255,255,.65);font-size:15px;margin-bottom:36px">{cta_sub}</p>
    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
      <a style="display:inline-flex;align-items:center;gap:7px;background:#fff;color:#0A0A0A;font-weight:800;padding:14px 40px;border-radius:100px;font-size:15px;text-decoration:none" href="#">{cta_copy} →</a>
      <a style="display:inline-flex;align-items:center;gap:7px;background:transparent;color:rgba(255,255,255,.8);font-weight:600;padding:13px 28px;border-radius:100px;border:1.5px solid rgba(255,255,255,.3);font-size:14px;text-decoration:none" href="#">카카오톡 문의</a>
    </div>
  </div>
</section>"""


# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #0E1119; }
[data-testid="stSidebar"] * { color: #C8D4EA !important; }
.stButton > button {
    background: linear-gradient(135deg,#FF6B35,#E84393);
    color: white; border: none; border-radius: 8px;
    font-weight: 700; width: 100%;
}
.stButton > button:hover { opacity: 0.88; }
.stSelectbox, .stTextInput, .stTextArea {
    background: #0B0F1C !important;
}
div[data-testid="stMetric"] {
    background: #0B0F1C; border: 1px solid #1E2640;
    border-radius: 8px; padding: 12px;
}
.preview-container {
    background: #060810; border-radius: 10px;
    border: 1px solid #1A1F2E; overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎓 강사 페이지 빌더 Pro")
    st.caption("컨셉별 프리미엄 랜딩페이지 생성기")
    st.divider()

    # API KEY
    st.markdown("**🔑 Gemini API Key**")
    api_key_input = st.text_input(
        "API Key", type="password",
        value=st.session_state.api_key,
        placeholder="AIzaSy...",
        help="aistudio.google.com에서 무료 발급",
        label_visibility="collapsed",
    )
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input

    if st.session_state.api_key:
        st.success("✓ API 키 입력됨 (무료 · 분당 15회)", icon="✅")
    else:
        st.info("👆 [aistudio.google.com](https://aistudio.google.com) → Get API Key", icon="🔑")

    st.divider()

    # CONCEPT SELECTION
    st.markdown("**🎨 페이지 컨셉**")
    concept_options = {k: v["label"] for k, v in THEMES.items()}
    if st.session_state.concept == "custom" and st.session_state.custom_theme:
        concept_options["custom"] = f"✦ {st.session_state.custom_theme.get('name', 'AI 커스텀')}"

    concept_cols = st.columns(2)
    theme_keys = list(THEMES.keys())
    for i, (key, theme) in enumerate(THEMES.items()):
        col = concept_cols[i % 2]
        with col:
            is_active = st.session_state.concept == key
            if st.button(
                theme["label"],
                key=f"theme_{key}",
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                st.session_state.concept = key
                st.session_state.custom_theme = None
                st.rerun()

    st.divider()

    # AI CONCEPT GENERATOR
    st.markdown("**✦ AI 컨셉 생성**")
    mood_input = st.text_area(
        "무드 묘사", height=80,
        placeholder="예: 사이버펑크 네온사인, 비오는 다크 도시\n예: 오래된 수학 교실 분필 칠판",
        value=st.session_state.ai_mood_input,
        label_visibility="collapsed",
    )
    st.session_state.ai_mood_input = mood_input

    col_gen, col_rand = st.columns(2)
    with col_gen:
        if st.button("✦ 생성", use_container_width=True):
            if not mood_input.strip():
                st.warning("무드를 입력해주세요")
            elif not st.session_state.api_key:
                st.warning("API 키를 먼저 입력해주세요")
            else:
                with st.spinner("AI 컨셉 생성 중..."):
                    try:
                        result = gen_concept(mood_input.strip())
                        st.session_state.custom_theme = result
                        st.session_state.concept = "custom"
                        st.success(f"✓ {result.get('name', '컨셉')} 생성됨!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"오류: {e}")
    with col_rand:
        if st.button("🎲 랜덤", use_container_width=True):
            if not st.session_state.api_key:
                st.warning("API 키를 먼저 입력해주세요")
            else:
                mood = random.choice(RANDOM_MOODS)
                st.session_state.ai_mood_input = mood
                with st.spinner(f"'{mood[:20]}...' 생성 중"):
                    try:
                        result = gen_concept(mood)
                        st.session_state.custom_theme = result
                        st.session_state.concept = "custom"
                        st.success(f"✓ {result.get('name', '컨셉')} 생성됨!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"오류: {e}")

    st.divider()

    # INSTRUCTOR INFO
    st.markdown("**👤 강사 정보**")
    col_name, col_subj = st.columns([3, 2])
    with col_name:
        name = st.text_input("강사명", value=st.session_state.instructor_name, placeholder="강사명", label_visibility="collapsed")
        st.session_state.instructor_name = name
    with col_subj:
        subj = st.selectbox("과목", ["영어", "수학", "국어", "사회", "과학"], index=["영어", "수학", "국어", "사회", "과학"].index(st.session_state.subject), label_visibility="collapsed")
        st.session_state.subject = subj

    if st.button("🔍 강사 정보 자동 검색", use_container_width=True):
        if not name:
            st.warning("강사명을 입력해주세요")
        elif not st.session_state.api_key:
            st.warning("API 키를 먼저 입력해주세요")
        else:
            with st.spinner(f"{name} 선생님 정보 검색 중..."):
                try:
                    profile = search_instructor(name, subj)
                    st.session_state.instructor_profile = profile
                    if profile.get("found"):
                        st.success(f"✓ {name} 선생님 정보 발견!")
                    else:
                        st.info("정보를 찾지 못했습니다. 직접 입력된 내용으로 생성합니다.")
                except Exception as e:
                    st.error(f"검색 실패: {e}")

    if st.session_state.instructor_profile and st.session_state.instructor_profile.get("found"):
        p = st.session_state.instructor_profile
        with st.expander("📋 검색된 강사 정보", expanded=False):
            if p.get("bio"):
                st.caption(f"**이력:** {p['bio'][:100]}...")
            if p.get("slogan"):
                st.caption(f"**슬로건:** {p['slogan']}")
            if p.get("signatureMethods"):
                st.caption(f"**학습법:** {', '.join(p['signatureMethods'])}")

    st.divider()

    # PAGE SETTINGS
    st.markdown("**📝 페이지 설정**")
    purpose = st.text_input("강의 브랜드명", value=st.session_state.purpose, placeholder="2026 수능 파이널 완성")
    st.session_state.purpose = purpose

    target = st.radio("수강 대상", ["고3·N수", "고1·2 — 기초 완성"], horizontal=True, index=0 if st.session_state.target == "고3·N수" else 1)
    st.session_state.target = target

    st.divider()

    # SECTIONS
    st.markdown("**📑 섹션 선택**")
    all_sections = {
        "banner": "🏠 메인 배너",
        "intro": "👤 강사 소개",
        "why": "💡 이유",
        "curriculum": "📚 커리큘럼",
        "target": "🎯 수강 대상",
        "reviews": "⭐ 수강평",
        "faq": "❓ FAQ",
        "cta": "📣 수강신청 CTA",
    }
    if "active_sections" not in st.session_state:
        st.session_state.active_sections = ["banner", "intro", "why", "curriculum", "cta"]

    for sec_id, sec_label in all_sections.items():
        checked = st.checkbox(sec_label, value=sec_id in st.session_state.active_sections, key=f"sec_{sec_id}")
        if checked and sec_id not in st.session_state.active_sections:
            st.session_state.active_sections.append(sec_id)
        elif not checked and sec_id in st.session_state.active_sections:
            st.session_state.active_sections.remove(sec_id)


# ─────────────────────────────────────────────
# MAIN AREA
# ─────────────────────────────────────────────
col_ctrl, col_preview = st.columns([1, 2], gap="large")

with col_ctrl:
    st.markdown("### ✍️ AI 문구 생성")

    copy_context = st.text_area(
        "페이지 맥락 설명",
        height=100,
        placeholder="예: 2026 수능 영어 파이널 완성 커리큘럼. 고3·N수 대상. 허어로·강사 소개·커리큘럼·수강후기 구성.\n예: 김철수 선생님의 수학 강의. ABPS 방법론으로 유명.",
        help="AI가 전체 문구를 생성하는 데 사용됩니다.",
    )

    if st.button("✦ 전체 문구 AI 생성", type="primary", use_container_width=True):
        if not copy_context.strip():
            st.warning("페이지 맥락을 입력해주세요")
        elif not st.session_state.api_key:
            st.warning("API 키를 먼저 입력해주세요")
        else:
            with st.spinner("AI가 전체 섹션 문구를 생성 중... (10~20초)"):
                try:
                    result = gen_copy(
                        copy_context,
                        st.session_state.instructor_name,
                        st.session_state.subject,
                        st.session_state.target,
                        st.session_state.purpose,
                    )
                    st.session_state.custom_copy = result
                    st.success("✓ 문구 생성 완료! 우측 미리보기를 확인하세요.")
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
        with st.expander("배너 섹션", expanded=False):
            bt = st.text_input("메인 제목", value=cp.get("bannerTitle", ""))
            bs = st.text_input("서브 키워드", value=cp.get("bannerSub", ""))
            bl = st.text_area("리드 문구", value=cp.get("bannerLead", ""), height=60)
            cc = st.text_input("버튼 텍스트", value=cp.get("ctaCopy", ""))
            if st.button("배너 적용", key="apply_banner"):
                st.session_state.custom_copy.update({"bannerTitle": bt, "bannerSub": bs, "bannerLead": bl, "ctaCopy": cc})
                st.success("적용됨!")
                st.rerun()

        with st.expander("강사 소개 섹션", expanded=False):
            it = st.text_input("소개 제목", value=cp.get("introTitle", ""))
            id_ = st.text_area("소개 본문", value=cp.get("introDesc", ""), height=60)
            ib = st.text_area("약력", value=cp.get("introBio", ""), height=60)
            if st.button("소개 적용", key="apply_intro"):
                st.session_state.custom_copy.update({"introTitle": it, "introDesc": id_, "introBio": ib})
                st.success("적용됨!")
                st.rerun()

        with st.expander("CTA 섹션", expanded=False):
            ct = st.text_area("CTA 제목 (<br> 줄바꿈)", value=cp.get("ctaTitle", ""), height=60)
            cs = st.text_input("CTA 서브문구", value=cp.get("ctaSub", ""))
            cb = st.text_input("뱃지 텍스트", value=cp.get("ctaBadge", ""))
            if st.button("CTA 적용", key="apply_cta"):
                st.session_state.custom_copy.update({"ctaTitle": ct, "ctaSub": cs, "ctaBadge": cb})
                st.success("적용됨!")
                st.rerun()
    else:
        st.caption("AI로 문구를 생성하면 여기서 직접 수정할 수 있습니다.")

    st.divider()

    # DOWNLOAD
    st.markdown("### 📥 HTML 내보내기")
    ordered_sections = [s for s in ["banner", "intro", "why", "curriculum", "target", "reviews", "faq", "cta"] if s in st.session_state.active_sections]
    final_html = build_html(ordered_sections)

    concept_name = st.session_state.concept
    if st.session_state.concept == "custom" and st.session_state.custom_theme:
        concept_name = st.session_state.custom_theme.get("name", "custom")

    st.download_button(
        label="📥 HTML 파일 다운로드",
        data=final_html.encode("utf-8"),
        file_name=f"{st.session_state.instructor_name or 'instructor'}_{st.session_state.subject}_{concept_name}.html",
        mime="text/html",
        use_container_width=True,
    )


with col_preview:
    st.markdown("### 👁 실시간 미리보기")

    theme_data = get_theme_data()
    current_concept = concept_name if st.session_state.concept == "custom" and st.session_state.custom_theme else THEMES.get(st.session_state.concept, {}).get("label", st.session_state.concept)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("컨셉", current_concept)
    with m2:
        st.metric("섹션 수", len(ordered_sections))
    with m3:
        st.metric("다크 모드", "ON" if theme_data["dark"] else "OFF")

    # Render HTML preview
    import streamlit.components.v1 as components
    components.html(final_html, height=900, scrolling=True)
