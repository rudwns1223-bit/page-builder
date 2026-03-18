"""강사 페이지 빌더 Pro v7.5"""
import streamlit as st
import requests
import json, re, time, random, base64

st.set_page_config(page_title="강사 페이지 빌더 Pro", page_icon="🎓",
    layout="wide", initial_sidebar_state="expanded")

_D = {
    "api_key":"","concept":"acid","custom_theme":None,
    "instructor_name":"","subject":"영어",
    "purpose_label":"2026 수능 파이널 완성","purpose_type":"신규 커리큘럼",
    "target":"고3·N수","custom_copy":None,"bg_photo_url":"",
    "active_sections":["banner","intro","why","curriculum","cta"],
    "ai_mood":"","inst_profile":None,"last_seed":None,
    "custom_section_on":False,"custom_section_topic":"",
    "uploaded_bg_b64":"","preview_ver":0,
}
for _k,_v in _D.items():
    if _k not in st.session_state: st.session_state[_k]=_v
if not st.session_state.api_key:
    try: st.session_state.api_key=st.secrets.get("GROQ_API_KEY","")
    except: pass

GROQ_URL="https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS=["llama-3.3-70b-versatile","llama3-70b-8192","mixtral-8x7b-32768"]

THEMES={
 "sakura":{"label":"🌸 벚꽃 봄","dark":False,"fonts":"https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;700&display=swap","vars":"--c1:#B5304A;--c2:#E89BB5;--c3:#F5CEDA;--c4:#2A111A;--bg:#FBF6F4;--bg2:#F7EFF1;--bg3:#F2E5E9;--text:#2A111A;--t70:rgba(42,17,26,.7);--t45:rgba(42,17,26,.45);--bd:rgba(42,17,26,.10);--fh:'Playfair Display','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:12px;--r-btn:100px;","extra_css":"","cta":"linear-gradient(135deg,#2A111A,#B5304A)","heroStyle":"editorial_bold","particle":"petals"},
 "fire":{"label":"🔥 다크 파이어","dark":True,"fonts":"https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@400;700;900&family=DM+Sans:wght@300;400;700&display=swap","vars":"--c1:#FF4500;--c2:#FF8C00;--c3:#FFD700;--c4:#0D0705;--bg:#0D0705;--bg2:#130A04;--bg3:#1A0E06;--text:#F1F5F9;--t70:rgba(241,245,249,.7);--t45:rgba(241,245,249,.45);--bd:rgba(255,69,0,.22);--fh:'Bebas Neue','Noto Sans KR',sans-serif;--fb:'DM Sans','Noto Sans KR',sans-serif;--r:4px;--r-btn:4px;","extra_css":"","cta":"linear-gradient(135deg,#0D0705,#FF4500 60%,#FF8C00)","heroStyle":"typographic","particle":"embers"},
 "ocean":{"label":"🌊 오션 블루","dark":False,"fonts":"https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap","vars":"--c1:#0EA5E9;--c2:#38BDF8;--c3:#BAE6FD;--c4:#0C4A6E;--bg:#F0F9FF;--bg2:#E0F2FE;--bg3:#BAE6FD;--text:#0C1A2E;--t70:rgba(12,26,46,.7);--t45:rgba(12,26,46,.45);--bd:rgba(14,165,233,.15);--fh:'Syne','Noto Sans KR',sans-serif;--fb:'Noto Sans KR',sans-serif;--r:10px;--r-btn:100px;","extra_css":"","cta":"linear-gradient(135deg,#0C4A6E,#0EA5E9)","heroStyle":"split","particle":"none"},
 "luxury":{"label":"✨ 골드 럭셔리","dark":True,"fonts":"https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,500;0,600;1,300;1,500&family=Noto+Serif+KR:wght@300;400;600&family=DM+Sans:wght@300;400;500&display=swap","vars":"--c1:#C8975A;--c2:#D4AF72;--c3:#EDD8A4;--c4:#0C0B09;--bg:#0C0B09;--bg2:#131108;--bg3:#1A1810;--text:#F5F0E8;--t70:rgba(245,240,232,.7);--t45:rgba(245,240,232,.45);--bd:rgba(200,151,90,.15);--fh:'Cormorant Garamond','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:2px;--r-btn:2px;","extra_css":".st{font-weight:300;font-style:italic}","cta":"linear-gradient(135deg,#0C0B09,#2A2010)","heroStyle":"editorial_bold","particle":"gold"},
 "cosmos":{"label":"🌌 코스모스","dark":True,"fonts":"https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Noto+Sans+KR:wght@300;400;700&family=DM+Sans:wght@300;400;500&display=swap","vars":"--c1:#7C3AED;--c2:#06B6D4;--c3:#A78BFA;--c4:#030712;--bg:#030712;--bg2:#080C18;--bg3:#0D1220;--text:#F1F5F9;--t70:rgba(241,245,249,.7);--t45:rgba(241,245,249,.45);--bd:rgba(124,58,237,.22);--fh:'Orbitron','Noto Sans KR',sans-serif;--fb:'DM Sans','Noto Sans KR',sans-serif;--r:0px;--r-btn:0px;","extra_css":".st{letter-spacing:.1em;text-transform:uppercase}","cta":"linear-gradient(135deg,#030712,#2D1B69)","heroStyle":"typographic","particle":"stars"},
 "winter":{"label":"❄️ 윈터 스노우","dark":False,"fonts":"https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,600;0,700;0,800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap","vars":"--c1:#1E40AF;--c2:#3B82F6;--c3:#BFDBFE;--c4:#0F172A;--bg:#F8FAFF;--bg2:#EFF6FF;--bg3:#DBEAFE;--text:#0F172A;--t70:rgba(15,23,42,.7);--t45:rgba(15,23,42,.45);--bd:rgba(30,64,175,.12);--fh:'Plus Jakarta Sans','Noto Sans KR',sans-serif;--fb:'Plus Jakarta Sans','Noto Sans KR',sans-serif;--r:8px;--r-btn:100px;","extra_css":".st{font-weight:800}","cta":"linear-gradient(135deg,#1E3A8A,#3B82F6)","heroStyle":"split","particle":"snow"},
 "eco":{"label":"🌿 에코 그린","dark":False,"fonts":"https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;500;700&display=swap","vars":"--c1:#059669;--c2:#34D399;--c3:#A7F3D0;--c4:#064E3B;--bg:#F0FDF4;--bg2:#DCFCE7;--bg3:#BBF7D0;--text:#064E3B;--t70:rgba(6,78,59,.7);--t45:rgba(6,78,59,.45);--bd:rgba(5,150,105,.15);--fh:'DM Serif Display','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:14px;--r-btn:100px;","extra_css":"","cta":"linear-gradient(135deg,#064E3B,#059669)","heroStyle":"split","particle":"leaves"},
 "cinematic":{"label":"🎬 시네마틱","dark":True,"fonts":"https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;500&display=swap","vars":"--c1:#FF1744;--c2:#FF5252;--c3:#4A0010;--c4:#050005;--bg:#050005;--bg2:#0A000A;--bg3:#150010;--text:#F8F0F0;--t70:rgba(248,240,240,.7);--t45:rgba(248,240,240,.45);--bd:rgba(255,23,68,.2);--fh:'Bebas Neue','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:0px;--r-btn:2px;","extra_css":".st{letter-spacing:.08em}","cta":"linear-gradient(135deg,#1A0005,#FF1744 55%,#FF5252)","heroStyle":"cinematic","particle":"embers"},
 "stadium":{"label":"🏟️ 스타디움","dark":True,"fonts":"https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Noto+Sans+KR:wght@400;700;900&family=DM+Sans:wght@300;400;500&display=swap","vars":"--c1:#FF2244;--c2:#FF6688;--c3:#3A0010;--c4:#020008;--bg:#020008;--bg2:#06000E;--bg3:#0C0018;--text:#F5F5FF;--t70:rgba(245,245,255,.7);--t45:rgba(245,245,255,.45);--bd:rgba(255,34,68,.22);--fh:'Black Han Sans','Noto Sans KR',sans-serif;--fb:'DM Sans','Noto Sans KR',sans-serif;--r:2px;--r-btn:2px;","extra_css":".st{letter-spacing:.04em}","cta":"linear-gradient(135deg,#020008,#FF2244 60%,#FF6688)","heroStyle":"typographic","particle":"none"},
 "acid":{"label":"⚡ 에시드 그린","dark":True,"fonts":"https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Noto+Sans+KR:wght@400;700;900&display=swap","vars":"--c1:#AAFF00;--c2:#CCFF44;--c3:#224400;--c4:#030703;--bg:#030703;--bg2:#060E06;--bg3:#0A1A0A;--text:#F0FFF0;--t70:rgba(240,255,240,.7);--t45:rgba(240,255,240,.45);--bd:rgba(170,255,0,.18);--fh:'Space Grotesk','Noto Sans KR',sans-serif;--fb:'Space Grotesk','Noto Sans KR',sans-serif;--r:0px;--r-btn:0px;","extra_css":".st{letter-spacing:.02em}.btn-p{color:#030703!important}","cta":"linear-gradient(135deg,#030703,#224400 40%,#AAFF00)","heroStyle":"typographic","particle":"none"},
 "floral":{"label":"🌸 플로럴 에디토리얼","dark":False,"fonts":"https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,600;0,700;1,300;1,600&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;500&display=swap","vars":"--c1:#E8386D;--c2:#F472A8;--c3:#FFD6E7;--c4:#1A0510;--bg:#FFFAF8;--bg2:#FFF0F4;--bg3:#FFE4EE;--text:#1A0510;--t70:rgba(26,5,16,.7);--t45:rgba(26,5,16,.45);--bd:rgba(232,56,109,.12);--fh:'Cormorant Garamond','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:0px;--r-btn:100px;","extra_css":".st{font-style:italic;font-weight:700}","cta":"linear-gradient(135deg,#1A0510,#E8386D)","heroStyle":"editorial_bold","particle":"petals"},
 "inception":{"label":"🌲 인셉션 에메랄드","dark":True,"fonts":"https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,600;1,300;1,600&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;500&display=swap","vars":"--c1:#2DB87C;--c2:#4ECFA0;--c3:#0A3020;--c4:#010C06;--bg:#010C06;--bg2:#031408;--bg3:#061C0C;--text:#E8F5F0;--t70:rgba(232,245,240,.7);--t45:rgba(232,245,240,.45);--bd:rgba(45,184,124,.18);--fh:'Cormorant Garamond','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:4px;--r-btn:4px;","extra_css":".st{font-style:italic}","cta":"linear-gradient(135deg,#010C06,#0A3020 50%,#2DB87C)","heroStyle":"editorial_bold","particle":"leaves"},
 "violet_pop":{"label":"💜 바이올렛 팝","dark":False,"fonts":"https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,600;0,700;0,800&family=Noto+Sans+KR:wght@400;500;700;900&display=swap","vars":"--c1:#7C3AED;--c2:#9F67FF;--c3:#EDE9FF;--c4:#1E0A3C;--bg:#FAFAFF;--bg2:#F5F3FF;--bg3:#EDE9FF;--text:#1E0A3C;--t70:rgba(30,10,60,.7);--t45:rgba(30,10,60,.45);--bd:rgba(124,58,237,.12);--fh:'Plus Jakarta Sans','Noto Sans KR',sans-serif;--fb:'Plus Jakarta Sans','Noto Sans KR',sans-serif;--r:16px;--r-btn:100px;","extra_css":".st{font-weight:800}","cta":"linear-gradient(135deg,#4C1D95,#7C3AED)","heroStyle":"split_bold","particle":"none"},
 "brutal":{"label":"◼️ 브루탈 모노","dark":False,"fonts":"https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Noto+Sans+KR:wght@400;700;900&display=swap","vars":"--c1:#1A1A1A;--c2:#444444;--c3:#E0E0E0;--c4:#000000;--bg:#F5F5F0;--bg2:#EBEBEB;--bg3:#E0E0E0;--text:#0A0A0A;--t70:rgba(10,10,10,.7);--t45:rgba(10,10,10,.45);--bd:rgba(10,10,10,.15);--fh:'Space Grotesk','Noto Sans KR',sans-serif;--fb:'Space Grotesk','Noto Sans KR',sans-serif;--r:0px;--r-btn:0px;","extra_css":".card{border:2px solid #0A0A0A!important;box-shadow:4px 4px 0 #0A0A0A!important}.btn-p{box-shadow:3px 3px 0 rgba(0,0,0,.3)!important}","cta":"linear-gradient(135deg,#0A0A0A,#333333)","heroStyle":"billboard","particle":"none"},
 "amber":{"label":"🟠 앰버 글로우","dark":True,"fonts":"https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Noto+Serif+KR:wght@300;400;600;900&family=DM+Sans:wght@300;400;500&display=swap","vars":"--c1:#F59E0B;--c2:#FCD34D;--c3:#7A4A00;--c4:#080400;--bg:#080400;--bg2:#0E0800;--bg3:#160D00;--text:#FFF8E8;--t70:rgba(255,248,232,.7);--t45:rgba(255,248,232,.45);--bd:rgba(245,158,11,.18);--fh:'Playfair Display','Noto Serif KR',serif;--fb:'DM Sans','Noto Serif KR',sans-serif;--r:4px;--r-btn:4px;","extra_css":".st{font-style:italic}","cta":"linear-gradient(135deg,#080400,#7A4A00 50%,#F59E0B)","heroStyle":"editorial_bold","particle":"gold"},
}

# ── 목적별 기본 추천 테마 (★ Fix 5)
PURPOSE_DEFAULT_THEME={"신규 커리큘럼":"inception","이벤트":"cinematic","기획전":"brutal"}

PURPOSE_SECTIONS={
 "신규 커리큘럼":["banner","intro","video","before_after","method","why","curriculum","target","package","reviews","faq","cta"],
 "이벤트":["banner","event_overview","event_benefits","event_deadline","reviews","cta"],
 "기획전":["fest_hero","fest_lineup","fest_benefits","fest_cta"],
}
PURPOSE_HINTS={
 "신규 커리큘럼":"📚 강사 전문성·신뢰감 강조 — 인셉션, 앰버, 코스모스 추천",
 "이벤트":"🎉 기간 한정·긴박감·혜택 강조 — 시네마틱, 에시드, 스타디움 추천",
 "기획전":"🏆 강사 라인업·통합 혜택 강조 — 브루탈, 골드 럭셔리, 코스모스 추천",
}
SEC_LABELS={
 "banner":"🏠 메인 배너","intro":"👤 강사 소개","why":"💡 필요한 이유",
 "curriculum":"📚 커리큘럼","target":"🎯 수강 대상","reviews":"⭐ 수강평",
 "faq":"❓ FAQ","cta":"📣 수강신청","video":"🎬 영상 미리보기",
 "before_after":"🔄 수강 전/후","method":"🧪 학습법 시각화","package":"📦 구성 안내",
 "event_overview":"📅 이벤트 개요","event_benefits":"🎁 이벤트 혜택","event_deadline":"⏰ 마감 안내",
 "fest_hero":"🏆 기획전 히어로","fest_lineup":"👥 강사 라인업","fest_benefits":"🎁 기획전 혜택","fest_cta":"📣 기획전 CTA",
 "custom_section":"✏️ 기타 섹션",
}
SUBJ_KW={
 "영어":["빈칸 추론","EBS 연계","순서·삽입","어법·어휘"],
 "수학":["수1·수2","미적분","확률과 통계","킬러 문항"],
 "국어":["독해력","문학","비문학","화법과 작문"],
 "사회":["생활과 윤리","한국지리","세계사","경제"],
 "과학":["물리학","화학","생명과학","지구과학"],
}
RANDOM_SEEDS=[
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
 {"mood":"앰버 황금빛 위스키 바 재즈 다크 고급 무드","layout":"editorial","font":"serif","particle":"gold"},
 {"mood":"바이올렛 퍼플 팝 컬러 현대적 밝은 에너지","layout":"modern","font":"sans","particle":"none"},
 {"mood":"브루탈리즘 건축 콘크리트 모노크롬 강렬한 타이포","layout":"brutal","font":"sans","particle":"none"},
 {"mood":"여름 밤 루프탑 인디고 블루 도시 스카이라인","layout":"immersive","font":"display","particle":"none"},
 {"mood":"가을 단풍 교정 은행나무 따뜻한 주황 갈색 노을","layout":"organic","font":"serif","particle":"leaves"},
]

# ══════════════════════════════════════════════════════
# ★ 배경 이미지 키워드 맵 v7.5 (200+ 항목)
# ══════════════════════════════════════════════════════
KO_BG={
 # 군중/사람
 "사람 많은":"crowd,people,busy,street","사람많은":"crowd,people,busy,street",
 "사람들":"crowd,people,street","군중":"crowd,stadium,people","붐비는":"crowded,busy,street",
 "인파":"crowd,people,festival","관중":"crowd,stadium,lights","관중석":"stadium,seats,crowd",
 "광장":"plaza,square,crowd","명동":"shopping,street,crowd,seoul","홍대":"street,neon,crowd,night",
 "이태원":"street,night,seoul,neon","강남":"city,modern,seoul,night","거리":"street,city,people",
 "시장":"market,people,busy,street",
 # 세계 랜드마크
 "에펠탑":"eiffel,tower,paris,france","에펠":"eiffel,paris,france","파리":"paris,france,city,night",
 "뉴욕":"new,york,manhattan,skyline","맨해튼":"manhattan,skyline,city,night",
 "타임스퀘어":"times,square,new,york,neon","런던":"london,city,night","빅벤":"big,ben,london",
 "도쿄":"tokyo,japan,city,night","시부야":"shibuya,crossing,tokyo,night","신주쿠":"shinjuku,neon,night",
 "홍콩":"hong,kong,skyline,night","싱가포르":"singapore,marina,bay,night",
 "두바이":"dubai,burj,khalifa,skyline","로마":"rome,colosseum,ancient","바티칸":"vatican,rome,italy",
 "베네치아":"venice,canal,italy","바르셀로나":"barcelona,spain,gaudi",
 "암스테르담":"amsterdam,canal,netherlands","프라하":"prague,castle,europe,night",
 "산토리니":"santorini,greece,white,blue","서울":"seoul,korea,city,skyline",
 "남산":"namsan,tower,seoul,night","한강":"han,river,seoul,night","경복궁":"gyeongbokgung,palace,korea",
 # 스포츠/경기장
 "야구장":"baseball,stadium,night,crowd","야구":"baseball,stadium,night",
 "경기장":"sports,arena,stadium,night","축구장":"soccer,field,stadium,lights",
 "축구":"soccer,football,pitch,green","농구장":"basketball,court,arena",
 "아레나":"sports,arena,crowd,night","올림픽":"olympic,stadium,sports",
 "수영장":"swimming,pool,water","트랙":"running,track,stadium",
 "격투":"martial,arts,fighting,ring","테니스":"tennis,court,sport","골프":"golf,course,green",
 # 자연
 "벚꽃":"cherry,blossom,pink,spring","단풍":"autumn,leaves,maple,fall",
 "숲":"forest,trees,nature,misty","자작나무":"birch,forest,white,trees",
 "겨울":"winter,snow,landscape,cold","눈":"snow,winter,white,landscape","눈밭":"snow,field,winter",
 "오로라":"aurora,northern,lights,sky","바다":"ocean,sea,waves,horizon",
 "해변":"beach,ocean,sand,waves","산":"mountain,peak,dramatic","설산":"snowy,mountain,peak,alpine",
 "폭포":"waterfall,nature,dramatic","들판":"field,meadow,golden","해바라기":"sunflower,field,yellow",
 "노을":"sunset,golden,sky,dramatic","일출":"sunrise,golden,horizon","은하수":"milky,way,stars,night",
 "호수":"lake,reflection,nature","계곡":"valley,river,forest","사막":"desert,sand,dunes",
 "정글":"jungle,rainforest,tropical","초원":"grassland,plains,savanna",
 # 건축/실내
 "도서관":"library,books,interior,shelves","책":"books,library,reading,study",
 "교실":"classroom,school,chalkboard","칠판":"chalkboard,classroom,school",
 "사찰":"temple,zen,peaceful,japan","교회":"church,cathedral,architecture",
 "성당":"cathedral,gothic,interior,light","박물관":"museum,art,interior,gallery",
 "미술관":"gallery,museum,art,interior","카페":"cafe,coffee,cozy,interior",
 "레스토랑":"restaurant,interior,fine,dining","호텔":"hotel,lobby,luxury,interior",
 "사무실":"office,workspace,modern","계단":"staircase,architecture,interior",
 "강당":"auditorium,hall,stage,seats","무대":"stage,theater,spotlight",
 "성":"castle,dark,dramatic,medieval","궁전":"palace,grand,architecture,gold",
 # 도시/야경
 "사이버펑크":"cyberpunk,neon,city,rain,night","네온":"neon,lights,night,colorful",
 "도시":"city,skyline,night,urban","루프탑":"rooftop,city,night,view",
 "밤거리":"street,night,city,lights","극장":"cinema,theater,dark,screen",
 "영화관":"cinema,theater,dark,screen","공연장":"concert,stage,lights,crowd",
 "클럽":"nightclub,neon,dark,party","바":"bar,night,drinks,moody",
 "지하철":"subway,metro,urban,tunnel","공항":"airport,terminal,travel,modern",
 # 학습/교육
 "수험생":"student,exam,study,library","강의실":"classroom,lecture,university",
 "공부":"study,books,desk,focus","집중":"focus,study,desk,lamp","대학교":"university,campus,academic",
 # 우주/신비
 "우주":"space,galaxy,nebula,cosmos","별":"stars,night,milky,way","은하":"galaxy,space,cosmos,stars",
 "혜성":"comet,space,stars,trail","행성":"planet,space,solar,system","블랙홀":"black,hole,space,dark",
 # 분위기/스타일
 "빈티지":"vintage,retro,film,grain","흑백":"monochrome,black,white,minimal",
 "앰버":"amber,golden,warm,cozy,dark","골드":"gold,luxury,dark,opulent",
 "불꽃":"fire,flames,dark,dramatic","안개":"fog,mist,atmospheric,moody",
 "연기":"smoke,dark,moody,dramatic","비":"rain,street,wet,urban,night",
 "폭우":"heavy,rain,storm,dramatic","먹구름":"storm,clouds,dramatic,dark",
 "번개":"lightning,storm,dramatic,sky","황혼":"dusk,twilight,golden,sky",
 # 이집트/역사
 "이집트":"egypt,pyramid,desert,ancient","피라미드":"pyramid,egypt,desert",
 "그리스":"greece,ancient,ruins,marble","로마시대":"roman,colosseum,ancient,ruins",
 # 강사/교육
 "강사":"teacher,education,classroom","강의":"lecture,presentation,speaker",
 "학생":"student,study,university,campus",
 # 국가/지역
 "프랑스":"france,paris,european,architecture","일본":"japan,tokyo,cherry,blossom",
 "미국":"usa,america,city,modern","유럽":"europe,architecture,historic,travel","아시아":"asia,city,night,neon",
 # 영어 직접 지원
 "baseball":"baseball,stadium,night","soccer":"soccer,football,field",
 "library":"library,books,interior","space":"space,galaxy,nebula",
 "fire":"fire,flames,dark","neon":"neon,lights,night","ocean":"ocean,sea,waves",
 "cinema":"cinema,theater,dark","stadium":"stadium,crowd,night",
 "mountain":"mountain,dramatic,peak","forest":"forest,trees,nature",
 "desert":"desert,sand,dunes","snow":"snow,winter,landscape","rain":"rain,street,wet",
 "crowd":"crowd,people,busy","eiffel":"eiffel,tower,paris","paris":"paris,france,city",
 "tokyo":"tokyo,japan,night","london":"london,city,night","newyork":"new,york,manhattan",
 "galaxy":"galaxy,space,nebula","aurora":"aurora,northern,lights",
 "vintage":"vintage,retro,film","cafe":"cafe,coffee,cozy",
}

def build_bg_url(mood:str)->str:
    """★ v7.5: 스마트 배경 이미지 (200+ 키워드 + 시맨틱 추출)"""
    if not mood: return ""
    text=mood.strip(); text_norm=text.lower().replace(" ","")
    found=[]
    # 1. 공백 포함 긴 구문 우선
    for ko,en in sorted(KO_BG.items(),key=lambda x:-len(x[0])):
        if ko.lower() in text.lower():
            found=en.split(","); break
    # 2. 공백 제거 후 붙여쓰기 매칭
    if not found:
        for ko,en in sorted(KO_BG.items(),key=lambda x:-len(x[0])):
            if ko.lower().replace(" ","") in text_norm:
                found=en.split(","); break
    # 3. 영어 단어 직접 추출
    if not found:
        stopwords={"this","that","with","from","have","been","dark","light","very"}
        eng=[w for w in re.findall(r"[a-zA-Z]{4,}",mood) if w.lower() not in stopwords]
        if eng: found=eng[:4]
    # 4. 한글 폴백
    if not found:
        hangul=re.findall(r"[가-힣]{2,}",mood)
        found=["dramatic","moody","atmospheric"] if not hangul else ["dramatic","dark","moody"]
    core=list(dict.fromkeys([k.strip() for k in found if k.strip()]))[:3]
    lock=random.randint(1,999999)
    return f"https://source.unsplash.com/1920x1080/?{','.join(core)}&sig={lock}"


# ══════════════════════════════════════════════════════
# ★ 테마별 코딩 효과 (v7.5 신규)
# ══════════════════════════════════════════════════════
THEME_FX={
 "acid":{
  "css":"",
  "html":"""<canvas id="fx-matrix" style="position:fixed;top:0;left:0;z-index:9997;pointer-events:none;opacity:.07"></canvas>
<script>(function(){var c=document.getElementById('fx-matrix');if(!c)return;var ctx=c.getContext('2d');
function rs(){c.width=window.innerWidth;c.height=window.innerHeight;}rs();window.addEventListener('resize',rs);
var cols=Math.floor(c.width/18);var drops=Array.from({length:cols},function(){return Math.random()*-80;});
var chars='01アイウエオABCDEF<>{}[]ΔΩΨΣ∞';
function draw(){ctx.fillStyle='rgba(3,7,3,0.04)';ctx.fillRect(0,0,c.width,c.height);
ctx.fillStyle='#AAFF00';ctx.font='13px monospace';
drops.forEach(function(d,i){ctx.fillText(chars[Math.floor(Math.random()*chars.length)],i*18,d*18);
if(d*18>c.height&&Math.random()>.975)drops[i]=0;drops[i]++;});}
setInterval(draw,50);})();</script>"""
 },
 "cinematic":{
  "css":""".fx-grain{position:fixed;inset:0;z-index:9997;pointer-events:none;opacity:.05;
animation:grain-anim .12s steps(2) infinite;
background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)'/%3E%3C/svg%3E");}
@keyframes grain-anim{0%{transform:translate(0,0)}25%{transform:translate(-2px,1px)}50%{transform:translate(1px,-2px)}75%{transform:translate(-1px,0)}100%{transform:translate(2px,-1px)}}
.fx-scanlines{position:fixed;inset:0;z-index:9996;pointer-events:none;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.05) 2px,rgba(0,0,0,.05) 4px)}
.fx-lbox-t,.fx-lbox-b{position:fixed;left:0;right:0;height:32px;background:#000;z-index:9998;pointer-events:none}
.fx-lbox-t{top:0}.fx-lbox-b{bottom:0}""",
  "html":'<div class="fx-grain"></div><div class="fx-scanlines"></div><div class="fx-lbox-t"></div><div class="fx-lbox-b"></div>'
 },
 "stadium":{
  "css":""".fx-spot{position:fixed;inset:0;z-index:9996;pointer-events:none;overflow:hidden}
.fx-sp{position:absolute;width:200px;height:600px;border-radius:50%;
background:radial-gradient(ellipse,rgba(255,255,255,.7),transparent 65%);
transform-origin:top center;animation:spot-sw 10s ease-in-out infinite}
.fx-sp:nth-child(1){left:8%;animation-delay:0s;opacity:.04}
.fx-sp:nth-child(2){left:42%;animation-delay:3.5s;opacity:.025}
.fx-sp:nth-child(3){right:10%;animation-delay:7s;opacity:.04}
@keyframes spot-sw{0%,100%{transform:rotate(-20deg)}50%{transform:rotate(20deg)}}
.fx-crowd{position:fixed;bottom:0;left:0;right:0;height:2px;z-index:9996;pointer-events:none;
background:linear-gradient(90deg,transparent,rgba(255,34,68,.6),rgba(255,100,136,.8),rgba(255,34,68,.6),transparent);
animation:crowd-p 2s ease-in-out infinite}
@keyframes crowd-p{0%,100%{opacity:.3}50%{opacity:.9}}""",
  "html":'<div class="fx-spot"><div class="fx-sp"></div><div class="fx-sp"></div><div class="fx-sp"></div></div><div class="fx-crowd"></div>'
 },
 "cosmos":{
  "css":"""@keyframes shoot{0%{transform:translateX(0) translateY(0) rotate(215deg);opacity:0}5%{opacity:.9}100%{transform:translateX(-500px) translateY(220px) rotate(215deg);opacity:0}}
.fx-shoot{position:fixed;top:12%;left:80%;width:2px;height:60px;pointer-events:none;z-index:9997;
background:linear-gradient(to bottom,rgba(255,255,255,0),rgba(255,255,255,.9));animation:shoot 6s ease-in infinite}
.fx-shoot:nth-child(2){top:28%;left:55%;animation-delay:2.2s}
.fx-shoot:nth-child(3){top:6%;left:40%;animation-delay:4.5s}
.fx-nebula{position:fixed;top:40%;left:50%;transform:translate(-50%,-50%);width:500px;height:350px;
border-radius:50%;pointer-events:none;z-index:9996;
background:radial-gradient(ellipse,rgba(124,58,237,.07),rgba(6,182,212,.03),transparent 70%);
animation:neb-p 9s ease-in-out infinite}
@keyframes neb-p{0%,100%{opacity:.5;transform:translate(-50%,-50%) scale(1)}50%{opacity:.9;transform:translate(-50%,-50%) scale(1.12)}}""",
  "html":'<div class="fx-shoot"></div><div class="fx-shoot"></div><div class="fx-shoot"></div><div class="fx-nebula"></div>'
 },
 "inception":{
  "css":"""@keyframes ring-cw{from{transform:translate(-50%,-50%) rotate(0deg)}to{transform:translate(-50%,-50%) rotate(360deg)}}
@keyframes ring-ccw{from{transform:translate(-50%,-50%) rotate(360deg)}to{transform:translate(-50%,-50%) rotate(0deg)}}
.fx-rings{position:fixed;top:50%;left:50%;pointer-events:none;z-index:9996}
.fx-r{position:absolute;border-radius:50%;border:1px solid rgba(45,184,124,.06);margin-left:-50%;margin-top:-50%}
.fx-r1{width:800px;height:800px;margin-left:-400px;margin-top:-400px;animation:ring-cw 40s linear infinite}
.fx-r2{width:560px;height:560px;margin-left:-280px;margin-top:-280px;animation:ring-ccw 26s linear infinite}
.fx-r3{width:360px;height:360px;margin-left:-180px;margin-top:-180px;animation:ring-cw 16s linear infinite}
.fx-r4{width:220px;height:220px;margin-left:-110px;margin-top:-110px;animation:ring-ccw 9s linear infinite}""",
  "html":'<div class="fx-rings"><div class="fx-r fx-r1"></div><div class="fx-r fx-r2"></div><div class="fx-r fx-r3"></div><div class="fx-r fx-r4"></div></div>'
 },
 "brutal":{
  "css":""".fx-grid{position:fixed;inset:0;z-index:9996;pointer-events:none;
background-image:linear-gradient(rgba(10,10,10,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(10,10,10,.05) 1px,transparent 1px);
background-size:80px 80px}
@keyframes glitch-1{0%,95%,100%{clip-path:none;transform:none}96%{clip-path:inset(20% 0 60% 0);transform:translateX(-4px)}97%{clip-path:inset(60% 0 20% 0);transform:translateX(4px)}98%{clip-path:none;transform:none}}
h1.st{animation:glitch-1 7s steps(1) infinite}""",
  "html":'<div class="fx-grid"></div>'
 },
 "amber":{
  "css":"""@keyframes amb-glow{0%,100%{opacity:.2;transform:translate(-50%,20%) scale(1)}50%{opacity:.45;transform:translate(-50%,20%) scale(1.18)}}
.fx-amb{position:fixed;bottom:0;left:50%;pointer-events:none;z-index:9996;
width:800px;height:550px;border-radius:50%;
background:radial-gradient(ellipse,rgba(245,158,11,.2),rgba(245,158,11,.05),transparent 65%);
animation:amb-glow 5s ease-in-out infinite}""",
  "html":'<div class="fx-amb"></div>'
 },
 "violet_pop":{
  "css":"@keyframes conf-fall{0%{transform:translateY(-30px) rotate(0deg);opacity:1}100%{transform:translateY(110vh) rotate(900deg);opacity:0}}.fx-conf{position:fixed;top:-30px;pointer-events:none;z-index:9997;animation:conf-fall linear infinite}",
  "html":"""<script>(function(){var c=['#7C3AED','#9F67FF','#EDE9FF','#C4B5FD','#A78BFA'];
for(var i=0;i<28;i++){var el=document.createElement('div');el.className='fx-conf';
var s=4+Math.random()*6,sh=Math.random()>.5;
el.style.cssText='left:'+Math.random()*100+'vw;width:'+s+'px;height:'+s+'px;background:'+c[Math.floor(Math.random()*c.length)]+';border-radius:'+(sh?'50%':'2px')+';animation-duration:'+(4+Math.random()*7)+'s;animation-delay:'+(-Math.random()*7)+'s';
document.body.appendChild(el);}})();</script>"""
 },
 "ocean":{
  "css":"""@keyframes wave-move{0%,100%{transform:translateX(0)}50%{transform:translateX(-22%)}}
.fx-wave{position:fixed;bottom:0;left:0;right:0;height:80px;pointer-events:none;z-index:9996;overflow:hidden}
.fx-wave svg{position:absolute;bottom:0;width:200%;animation:wave-move 7s ease-in-out infinite;opacity:.1}""",
  "html":'<div class="fx-wave"><svg viewBox="0 0 1440 80" xmlns="http://www.w3.org/2000/svg"><path d="M0,40 C240,80 480,0 720,40 C960,80 1200,0 1440,40 L1440,80 L0,80 Z" fill="#0EA5E9"/></svg></div>'
 },
 "fire":{
  "css":"""@keyframes fire-pulse{0%,100%{opacity:.12}50%{opacity:.22}}
.fx-fire-aura{position:fixed;bottom:0;left:0;right:0;height:180px;pointer-events:none;z-index:9996;
background:linear-gradient(to top,rgba(255,69,0,.15),rgba(255,140,0,.05),transparent);
animation:fire-pulse 3s ease-in-out infinite}""",
  "html":'<div class="fx-fire-aura"></div>'
 },
 "luxury":{
  "css":"""@keyframes lux-shimmer{0%{background-position:200% center}100%{background-position:-200% center}}
.fx-lux-line{position:fixed;top:0;left:0;right:0;height:2px;pointer-events:none;z-index:9998;
background:linear-gradient(90deg,transparent,#C8975A,#F5C842,#C8975A,transparent);
background-size:200% 100%;animation:lux-shimmer 4s linear infinite}""",
  "html":'<div class="fx-lux-line"></div>'
 },
 "floral":{
  "css":"@keyframes floral-drift{0%,100%{transform:translateX(0) rotate(0deg)}50%{transform:translateX(12px) rotate(6deg)}}.fx-bloom{position:fixed;pointer-events:none;z-index:9997;font-size:1.6em;opacity:.07;animation:floral-drift ease-in-out infinite}",
  "html":"""<script>(function(){var b=['🌸','🌺','🌼','✿','❀','🌷'];
var pos=[{top:'10%',left:'4%',d:'6s'},{top:'28%',right:'6%',d:'8s'},{bottom:'22%',left:'3%',d:'7s'},{bottom:'15%',right:'4%',d:'9s'}];
pos.forEach(function(p,i){var el=document.createElement('div');el.className='fx-bloom';
el.textContent=b[i%b.length];Object.assign(el.style,p);el.style.animationDuration=p.d;el.style.animationDelay=(-Math.random()*5)+'s';
document.body.appendChild(el);});})();</script>"""
 },
 "sakura":{"css":"","html":""},"winter":{"css":"","html":""},"eco":{"css":"","html":""},
 "custom":{"css":"","html":""},
}

def _theme_effects_html(concept:str)->str:
    fx=THEME_FX.get(concept,THEME_FX.get("custom",{"css":"","html":""}))
    css_part=f"<style>{fx['css']}</style>" if fx.get("css") else ""
    return css_part+fx.get("html","")


# ══════════════════════════════════════════════════════
# 유틸 / AI 호출
# ══════════════════════════════════════════════════════
def strip_hanja(t):
    if not isinstance(t,str): return str(t) if t is not None else ""
    return "".join(c for c in t if not(0x4E00<=ord(c)<=0x9FFF or 0x3400<=ord(c)<=0x4DBF)).strip()

def clean_obj(o):
    if isinstance(o,str): return strip_hanja(o)
    if isinstance(o,dict): return {k:clean_obj(v) for k,v in o.items()}
    if isinstance(o,list): return [clean_obj(i) for i in o]
    return o

def safe_json(raw:str)->dict:
    s=re.sub(r"```json\s*","",raw.strip()); s=re.sub(r"```\s*","",s).strip()
    start=s.find("{")
    if start<0: raise ValueError(f"JSON 파싱 실패: {raw[:200]}")
    s=s[start:]
    depth,end_idx=0,-1; in_str=escape=False
    for i,ch in enumerate(s):
        if escape: escape=False; continue
        if ch=="\\": escape=True; continue
        if ch=='"' and not escape: in_str=not in_str; continue
        if in_str: continue
        if ch=="{": depth+=1
        elif ch=="}":
            depth-=1
            if depth==0: end_idx=i; break
    if end_idx<0: raise ValueError(f"JSON 파싱 실패: {raw[:200]}")
    candidate=s[:end_idx+1]
    def _t(x):
        try: return clean_obj(json.loads(x))
        except: return None
    r=_t(candidate) or _t(candidate.replace("\n"," "))
    if r: return r
    fixed=re.sub(r",\s*}","}",re.sub(r",\s*]","]",candidate))
    r=_t(fixed)
    if r: return r
    raise ValueError(f"AI 파싱 실패: {raw[:200]}")

def call_ai(prompt:str,system:str="",max_tokens:int=2000)->str:
    key=st.session_state.api_key.strip()
    if not key: raise ValueError("API 키가 없습니다.")
    msgs=[{"role":"system","content":(system+"\n\n" if system else "")+"Return ONLY valid JSON. No markdown. No extra text. Never use Chinese characters. Write in Korean only."},
          {"role":"user","content":prompt}]
    last_err=None
    for model in GROQ_MODELS:
        try:
            resp=requests.post(GROQ_URL,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
                json={"model":model,"messages":msgs,"max_tokens":max_tokens,"temperature":0.75},timeout=60)
        except Exception as e: last_err=Exception(f"네트워크 오류: {e}"); continue
        if resp.status_code==401: raise Exception("🔑 API 키 오류")
        if resp.status_code==429: last_err=Exception(f"⏳ 한도 초과({model})"); time.sleep(2); continue
        if not resp.ok:
            try: msg=resp.json().get("error",{}).get("message",resp.text[:150])
            except: msg=resp.text[:150]
            last_err=Exception(f"HTTP {resp.status_code}: {msg}"); continue
        try:
            text=resp.json()["choices"][0]["message"]["content"]
            if text and text.strip(): return text
        except Exception as e: last_err=Exception(f"응답 파싱 실패: {e}"); continue
    raise last_err or Exception("모든 모델 실패")

INSTRUCTOR_DB={
 "이명학":{"found":True,"subject":"영어","bio":"대성마이맥 영어 강사. R'gorithm·Syntax·Read N' Logic 시리즈.","slogan":"영어, 논리로 끝낸다","signatureMethods":["R'gorithm","Syntax"],"teachingStyle":"구문 분석과 독해 논리 체계적 연결","desc":"R'gorithm으로 지문 구조를 논리적으로 파악"},
 "션티":{"found":True,"subject":"영어","bio":"대성마이맥 영어 강사. KISS 시리즈(KISSAVE·KISSCHEMA·KISS Logic).","slogan":"KISS — Keep It Simple, Suneung","signatureMethods":["KISS Logic","KISSAVE","KISSCHEMA"],"teachingStyle":"수능 영어 핵심 원리를 KISS로 단순화 반복 훈련","desc":"KISS 시리즈로 처음부터 끝까지 수능 영어 완성"},
 "이미지":{"found":True,"subject":"수학","bio":"대성마이맥 수학 강사. 세젤쉬·미친개념·미친기분 시리즈.","slogan":"수학, 미치도록 쉽게","signatureMethods":["세젤쉬","미친개념","미친기분"],"teachingStyle":"복잡한 개념을 직관적으로 쉽게","desc":"세젤쉬·미친개념으로 수학 입문자도 따라오게 만드는 강사"},
 "김범준":{"found":True,"subject":"수학","bio":"대성마이맥 수학. Starting Block·KICE Anatomy·The Hurdling.","slogan":"수능 수학의 뼈대를 세워라","signatureMethods":["KICE Anatomy","Starting Block","The Hurdling"],"teachingStyle":"수능 기출 해부로 출제 원리 파악","desc":"KICE Anatomy로 수능 수학 기출 원리 완전 이해"},
 "김승리":{"found":True,"subject":"국어","bio":"대성마이맥 국어. All Of KICE·VIC-FLIX 시리즈.","slogan":"국어, 승리로 끝낸다","signatureMethods":["All Of KICE","VIC-FLIX"],"teachingStyle":"수능 국어 출제 원리 파악 후 실전 능력 강화","desc":"All Of KICE로 국어 원리부터 실전까지 완성"},
 "유대종":{"found":True,"subject":"국어","bio":"대성마이맥 국어. 인셉션 시리즈·파노라마·O.V.S.","slogan":"국어의 인셉션을 시작하라","signatureMethods":["인셉션","O.V.S","파노라마"],"teachingStyle":"인셉션 방식으로 국어 깊이 이해","desc":"인셉션 시리즈로 국어 원리 차근차근 이해"},
}

def search_instructor(name:str,subj:str)->dict:
    if name in INSTRUCTOR_DB: return INSTRUCTOR_DB[name]
    for db_name,info in INSTRUCTOR_DB.items():
        if name in db_name or db_name in name: return info
    prompt=f'한국 수능 강사 "{name}" ({subj}). 확실히 아는 정보만. 한자 금지.\nJSON만: {{"found":true,"bio":"1문장","slogan":"","signatureMethods":[],"teachingStyle":"1문장","desc":"1문장"}}'
    try: return safe_json(call_ai(prompt,max_tokens=300))
    except: return {"found":True,"bio":f"{subj} 강사","slogan":"","signatureMethods":[],"teachingStyle":"","desc":""}

def _get_instructor_context()->str:
    ip=st.session_state.get("inst_profile") or {}
    name=st.session_state.instructor_name; subj=st.session_state.subject
    if not ip.get("found") or not name: return f"강사명: {name} | 과목: {subj}" if name else f"과목: {subj}"
    parts=[f"강사: {name} ({subj})"]
    if ip.get("bio"): parts.append(f"이력: {ip['bio']}")
    if ip.get("slogan"): parts.append(f"슬로건: \"{ip['slogan']}\"")
    methods=[m for m in (ip.get("signatureMethods") or []) if m and m!="없음"]
    if methods: parts.append(f"고유 학습법: {', '.join(methods)}")
    if ip.get("teachingStyle"): parts.append(f"강의 스타일: {ip['teachingStyle']}")
    if ip.get("desc"): parts.append(f"차별점: {ip['desc']}")
    return "\n".join(parts)

def gen_copy(ctx:str,ptype:str,tgt:str,plabel:str)->dict:
    inst_ctx=_get_instructor_context()
    schemas={
     "신규 커리큘럼":'{"bannerSub":"10자","bannerTitle":"20자","brandTagline":"컨셉 브랜드 한 문장","bannerLead":"60-90자 수험생 공감 리드","ctaCopy":"10자","ctaTitle":"CTA 제목","ctaSub":"30자","ctaBadge":"15자","statBadges":[],"introTitle":"20자","introDesc":"80-120자 강사 차별점","introBio":"60자이내","introBadges":[],"whyTitle":"20자","whySub":"30자","whyReasons":[["이모지","12자","60자"],["이모지","12자","60자"],["이모지","12자","60자"]],"curriculumTitle":"20자","curriculumSub":"30자","curriculumSteps":[["01","8자","50자이상","4주"],["02","8자","50자이상","4주"],["03","8자","50자이상","3주"],["04","8자","50자이상","3주"]],"targetTitle":"20자","targetItems":["40자이상","40자이상","40자이상","40자이상"],"reviews":[["50-70자 인용문","이름","뱃지"],["50-70자","이름","뱃지"],["50-70자","이름","뱃지"]],"faqs":[["15자 질문","50자이상 답변"],["질문","50자이상"],["질문","50자이상"]],"videoTitle":"20자","videoSub":"40자","videoTag":"OFFICIAL TRAILER","baTitle":"20자","baSub":"30자","baBeforeItems":["40자","40자","40자"],"baAfterItems":["40자","40자","40자"],"methodTitle":"20자","methodSub":"30자","methodSteps":[{"step":"STEP 01","label":"단계명","desc":"45자이상"},{"step":"STEP 02","label":"단계명","desc":"45자이상"},{"step":"STEP 03","label":"단계명","desc":"45자이상"}],"pkgTitle":"20자","pkgSub":"30자","packages":[{"icon":"📗","name":"구성명","desc":"40자이상","badge":"필수"},{"icon":"📖","name":"구성명","desc":"40자이상","badge":"포함"},{"icon":"🎯","name":"구성명","desc":"40자이상","badge":"포함"},{"icon":"💬","name":"구성명","desc":"40자이상","badge":"특전"}]}',
     "이벤트":'{"bannerSub":"10자","bannerTitle":"20자","brandTagline":"이벤트 분위기 한 문장","bannerLead":"60-80자 긴박감","ctaCopy":"10자","ctaTitle":"CTA","ctaSub":"30자","ctaBadge":"15자","statBadges":[],"eventTitle":"20자","eventDesc":"50자이상","eventDetails":[["📅","이벤트 기간","날짜"],["🎯","대상","값"],["💰","혜택","값"]],"benefitsTitle":"20자","eventBenefits":[{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"01"},{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"02"},{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"03"}],"deadlineTitle":"20자","deadlineMsg":"70자 긴박감","reviews":[["50-70자","이름","뱃지"],["인용문","이름","뱃지"],["인용문","이름","뱃지"]]}',
     "기획전":'{"festHeroTitle":"20자","festHeroCopy":"30자","festHeroSub":"50자이상","brandTagline":"기획전 분위기 한 문장","festHeroStats":[["수치","라벨"],["수치","라벨"],["수치","라벨"],["수치","라벨"]],"festLineupTitle":"20자","festLineupSub":"40자","festLineup":[{"name":"강사명","tag":"분야8자","tagline":"강사 소개 40자","badge":"8자","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"소개 40자","badge":"뱃지","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"소개 40자","badge":"뱃지","emoji":"이모지"},{"name":"강사명","tag":"분야","tagline":"소개 40자","badge":"뱃지","emoji":"이모지"}],"festBenefitsTitle":"20자","festBenefits":[{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"01"},{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"02"},{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"03"},{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"04"}],"festCtaTitle":"CTA제목","festCtaSub":"50자이상"}',
    }
    prompt=f"""대한민국 최고 수능 교육 랜딩페이지 카피라이터.
===강사 정보===\n{inst_ctx}\n===페이지 정보===\n맥락: "{ctx}"\n목적: {ptype} | 대상: {tgt} | 브랜드: {plabel}
규칙: 강사 고유 학습법 직접 사용, 현대적 어조, 한자 금지, 수치 금지, 순수 한국어만
JSON만: {schemas.get(ptype,schemas["신규 커리큘럼"])}"""
    return safe_json(call_ai(prompt,max_tokens=3500))

def gen_section(sec_id:str)->dict:
    inst_ctx=_get_instructor_context()
    schemas={
     "banner":'{"bannerSub":"10자","bannerTitle":"20자","brandTagline":"컨셉 한 문장","bannerLead":"60-90자","ctaCopy":"10자","statBadges":[]}',
     "intro":'{"introTitle":"20자","introDesc":"80-120자","introBio":"60자","introBadges":[]}',
     "why":'{"whyTitle":"20자","whySub":"30자","whyReasons":[["이모지","12자","60자"],["이모지","12자","60자"],["이모지","12자","60자"]]}',
     "curriculum":'{"curriculumTitle":"20자","curriculumSub":"30자","curriculumSteps":[["01","8자","50자이상","기간"],["02","8자","50자이상","기간"],["03","8자","50자이상","기간"],["04","8자","50자이상","기간"]]}',
     "target":'{"targetTitle":"20자","targetItems":["40-50자 구체적 상황","항목2 40자","항목3 40자","항목4 40자"]}',
     "reviews":'{"reviews":[["50-70자 인용문","이름","뱃지"],["50-70자","이름","뱃지"],["50-70자","이름","뱃지"]]}',
     "faq":'{"faqs":[["15자 질문","50자이상 답변"],["질문","50자이상"],["질문","50자이상"]]}',
     "cta":'{"ctaTitle":"CTA제목","ctaSub":"40자이상","ctaCopy":"10자","ctaBadge":"15자"}',
     "event_overview":'{"eventTitle":"20자","eventDesc":"50자이상","eventDetails":[["📅","이벤트 기간","날짜"],["🎯","대상","값"],["💰","혜택","값"]]}',
     "event_benefits":'{"benefitsTitle":"20자","eventBenefits":[{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"01"},{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"02"},{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"03"}]}',
     "event_deadline":'{"deadlineTitle":"15자","deadlineMsg":"70자이상","ctaCopy":"10자"}',
     "fest_hero":'{"festHeroTitle":"20자","festHeroCopy":"30자","festHeroSub":"50자이상","brandTagline":"한 문장","festHeroStats":[["수치","라벨"],["수치","라벨"]]}',
     "fest_lineup":'{"festLineupTitle":"20자","festLineupSub":"40자","festLineup":[{"name":"강사명","tag":"8자","tagline":"40자","badge":"8자","emoji":"이모지"},{"name":"강사명","tag":"8자","tagline":"40자","badge":"8자","emoji":"이모지"},{"name":"강사명","tag":"8자","tagline":"40자","badge":"8자","emoji":"이모지"},{"name":"강사명","tag":"8자","tagline":"40자","badge":"8자","emoji":"이모지"}]}',
     "fest_benefits":'{"festBenefitsTitle":"20자","festBenefits":[{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"01"},{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"02"},{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"03"},{"icon":"이모지","title":"혜택명","desc":"50자이상","badge":"8자","no":"04"}]}',
     "fest_cta":'{"festCtaTitle":"20자","festCtaSub":"50자이상"}',
     "video":'{"videoTitle":"20자","videoSub":"40자","videoTag":"OFFICIAL TRAILER","videoUrl":""}',
     "before_after":'{"baTitle":"20자","baSub":"30자","baBeforeItems":["40자","40자","40자"],"baAfterItems":["40자","40자","40자"]}',
     "method":'{"methodTitle":"20자","methodSub":"30자","methodSteps":[{"step":"STEP 01","label":"단계명","desc":"40자이상"},{"step":"STEP 02","label":"단계명","desc":"40자이상"},{"step":"STEP 03","label":"단계명","desc":"40자이상"}]}',
     "package":'{"pkgTitle":"20자","pkgSub":"30자","packages":[{"icon":"📗","name":"구성명","desc":"40자이상","badge":"필수"},{"icon":"📖","name":"구성명","desc":"40자이상","badge":"포함"},{"icon":"🎯","name":"구성명","desc":"40자이상","badge":"포함"},{"icon":"💬","name":"구성명","desc":"40자이상","badge":"특전"}]}',
    }
    sec_name=SEC_LABELS.get(sec_id,sec_id)
    prompt=f'수능 교육 카피라이터. "{sec_name}" 섹션만 새롭게 생성.\n{inst_ctx}\n과목: {st.session_state.subject} | 브랜드: {st.session_state.purpose_label}\n규칙: 강사 고유 학습법 사용, 현대적 어조, 한자 금지, 수치 금지, 순수 한국어만\nJSON만: {schemas.get(sec_id,"{}")}'
    return safe_json(call_ai(prompt,max_tokens=900))

def gen_concept(seed:dict)->dict:
    mood=seed.get("mood","")
    MOOD_HINTS={"야구장":"배경 #020008, 강조색 #FF2244 레드, 레이아웃 typographic","사이버펑크":"배경 #020008, 강조색 #A855F7 보라+#06B6D4 사이언","이집트":"배경 #0A0600, 강조색 #C8975A 골드, 레이아웃 editorial_bold","우주":"배경 #030712, 강조색 #7C3AED 보라, 레이아웃 typographic","불꽃":"배경 #0D0705, 강조색 #FF4500, 레이아웃 typographic","벚꽃":"배경 #FBF6F4 밝은, 강조색 #E8386D, 레이아웃 editorial_bold","에시드":"배경 #030703, 강조색 #AAFF00, 레이아웃 typographic"}
    color_hint=""
    for kw,hint in MOOD_HINTS.items():
        if kw.lower() in mood.lower(): color_hint=f"\n⚠️ 색상 필수 지침: {hint}"; break
    prompt=f"""한국 교육 랜딩페이지 RADICAL 디자이너. 무드: "{mood}"{color_hint}
규칙: bg 어두우면 textHex #E0 이상, bg 밝으면 textHex #111~#333. displayFont는 실제 Google Fonts만.
heroStyle: typographic/cinematic/billboard/editorial_bold/split/immersive 중 무드에 맞게.
JSON만: {{"name":"2-4글자+이모지","dark":true,"heroStyle":"typographic","c1":"#hex","c2":"#hex","c3":"#hex","c4":"#hex","bg":"#hex","bg2":"#hex","bg3":"#hex","textHex":"#hex","textRgb":"r,g,b","bdAlpha":"rgba(r,g,b,.15)","displayFont":"Font Name","bodyFont":"Noto Sans KR","fontWeights":"400;700;900","displayFontWeights":"400;700","borderRadiusPx":0,"btnBorderRadiusPx":2,"particle":"{seed.get("particle","none")}","ctaGradient":"linear-gradient(135deg,#hex,#hex)"}}"""
    result=safe_json(call_ai(prompt,max_tokens=1200))
    if not result.get("name") or len(result.get("name",""))>12: result["name"]=mood.split()[0][:4]+" 🎨"
    ml=mood.lower()
    if result.get("particle","none")=="none":
        if any(k in ml for k in ["눈","겨울","snow"]): result["particle"]="snow"
        elif any(k in ml for k in ["벚꽃","봄","floral"]): result["particle"]="petals"
        elif any(k in ml for k in ["우주","별","cosmos"]): result["particle"]="stars"
        elif any(k in ml for k in ["불꽃","ember"]): result["particle"]="embers"
        elif any(k in ml for k in ["황금","gold","이집트","앰버"]): result["particle"]="gold"
        elif any(k in ml for k in ["단풍","낙엽","숲"]): result["particle"]="leaves"
    return _ensure_contrast(result)

def gen_custom_sec(topic:str)->dict:
    inst_ctx=_get_instructor_context()
    prompt=f'수능 교육 랜딩페이지 추가 섹션. {inst_ctx}\n과목: {st.session_state.subject}\n주제: "{topic}"\n규칙: 반드시 "{topic}" 주제로만 작성, 한자 금지\nJSON만: {{"tag":"{topic[:6]}","title":"{topic} 안내","desc":"60자내외 설명","items":[{{"icon":"이모지","title":"15자이내","desc":"45자이상"}},{{"icon":"이모지","title":"15자이내","desc":"45자이상"}},{{"icon":"이모지","title":"15자이내","desc":"45자이상"}}]}}'
    return safe_json(call_ai(prompt,max_tokens=700))

def _hex_luminance(h:str)->float:
    try:
        h=h.lstrip("#")
        if len(h)==3: h="".join(c*2 for c in h)
        r,g,b=int(h[0:2],16)/255,int(h[2:4],16)/255,int(h[4:6],16)/255
        def lin(v): return v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4
        return 0.2126*lin(r)+0.7152*lin(g)+0.0722*lin(b)
    except: return 0.5

def _ensure_contrast(ct:dict)->dict:
    bg_l=_hex_luminance(ct.get("bg","#111")); tx_l=_hex_luminance(ct.get("textHex","#fff"))
    ratio=(max(bg_l,tx_l)+0.05)/(min(bg_l,tx_l)+0.05)
    if ratio<3.5:
        if bg_l<0.18: ct["textHex"]="#F0F0F0"; ct["textRgb"]="240,240,240"
        else: ct["textHex"]="#111111"; ct["textRgb"]="17,17,17"
    return ct

def get_theme()->dict:
    if st.session_state.concept=="custom" and st.session_state.custom_theme:
        ct=_ensure_contrast(st.session_state.custom_theme)
        df=ct.get("displayFont","Noto Sans KR"); bf=ct.get("bodyFont","Noto Sans KR")
        fw=ct.get("fontWeights","400;700;900"); dfw=ct.get("displayFontWeights","400;700")
        r=ct.get("borderRadiusPx",4); rb=ct.get("btnBorderRadiusPx",4)
        tr=ct.get("textRgb","255,255,255"); bd=ct.get("bdAlpha","rgba(255,255,255,.12)")
        _nw=["Black Han Sans","Bebas Neue","Orbitron"]
        if df in _nw:
            fonts=f"https://fonts.googleapis.com/css2?family={df.replace(' ','+')}"+f"&family={bf.replace(' ','+')}:wght@{fw}&display=swap"
        else:
            fonts=f"https://fonts.googleapis.com/css2?family={df.replace(' ','+')}:wght@{dfw}&family={bf.replace(' ','+')}:wght@{fw}&display=swap"
        v=(f"--c1:{ct['c1']};--c2:{ct['c2']};--c3:{ct['c3']};--c4:{ct['c4']};"
           f"--bg:{ct['bg']};--bg2:{ct['bg2']};--bg3:{ct['bg3']};"
           f"--text:{ct['textHex']};--t70:rgba({tr},.7);--t45:rgba({tr},.45);"
           f"--bd:{bd};--fh:'{df}','Noto Serif KR',serif;--fb:'{bf}',sans-serif;--r:{r}px;--r-btn:{rb}px;")
        return {"fonts":fonts,"vars":v,"extra_css":ct.get("extraCSS",""),
                "dark":ct.get("dark",True),"heroStyle":ct.get("heroStyle","typographic"),
                "cta":ct.get("ctaGradient",f"linear-gradient(135deg,{ct['c4']},{ct['c1']})"),"particle":ct.get("particle","none")}
    t=THEMES.get(st.session_state.concept,THEMES["acid"])
    return {"fonts":t["fonts"],"vars":t["vars"],"extra_css":t.get("extra_css",""),
            "dark":t.get("dark",True),"heroStyle":t.get("heroStyle","typographic"),
            "cta":t.get("cta","linear-gradient(135deg,var(--c4),var(--c1))"),"particle":t.get("particle","none")}


# ══════════════════════════════════════════════════════
# CSS — 모바일 완전 대응 (★ Fix 3)
# ══════════════════════════════════════════════════════
BASE_CSS="""
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:var(--fb);background:var(--bg);color:var(--text);overflow-x:hidden;-webkit-font-smoothing:antialiased}
a{text-decoration:none;color:inherit}
h1,h2,h3,p,span,div{word-break:keep-all;overflow-wrap:break-word}
.rv{opacity:0;transform:translateY(22px);transition:opacity .9s cubic-bezier(.16,1,.3,1),transform .9s cubic-bezier(.16,1,.3,1)}
.rv.on{opacity:1;transform:none}
.d1{transition-delay:.12s}.d2{transition-delay:.26s}.d3{transition-delay:.42s}.d4{transition-delay:.58s}
@keyframes pulse-accent{0%,100%{opacity:.6}50%{opacity:1}}
.btn-p{display:inline-flex;align-items:center;gap:8px;background:var(--c1);color:#fff;
  font-family:var(--fb);font-size:14px;font-weight:800;padding:14px 32px;
  border-radius:var(--r-btn,4px);border:none;cursor:pointer;
  box-shadow:0 4px 24px rgba(0,0,0,.25);transition:opacity .15s,transform .15s;
  text-decoration:none;letter-spacing:.02em;white-space:nowrap}
.btn-p:hover{opacity:.88;transform:translateY(-2px);box-shadow:0 8px 32px rgba(0,0,0,.35)}
.sec{padding:clamp(60px,8vw,96px) clamp(28px,6vw,80px);position:relative}
.sec.alt{background:var(--bg2)}
.tag-line{display:inline-flex;align-items:center;gap:9px;font-size:9.5px;font-weight:800;
  letter-spacing:.18em;text-transform:uppercase;color:var(--c1);margin-bottom:14px}
.tag-line::before{content:'';display:block;width:24px;height:2px;background:var(--c1)}
.sec-h2{font-family:var(--fh);font-size:clamp(24px,3.5vw,40px);font-weight:900;
  line-height:1.15;letter-spacing:-.04em;color:var(--text);margin-bottom:12px}
.sec-sub{font-size:14px;line-height:1.9;color:var(--t70);margin-bottom:36px;max-width:560px}
.card{background:var(--bg);border:1px solid var(--bd);border-radius:var(--r,4px);
  padding:24px;transition:transform .25s,box-shadow .25s}
.card:hover{transform:translateY(-4px);box-shadow:0 12px 40px rgba(0,0,0,.12)}
/* ─ 모바일 (≤900px) ─ */
@media(max-width:900px){
  .sec{padding:clamp(44px,8vw,68px) clamp(18px,5vw,32px)}
  [style*="grid-template-columns:1fr 1.4fr"],[style*="grid-template-columns:1fr 1.6fr"],
  [style*="grid-template-columns:1fr 1.8fr"],[style*="grid-template-columns:1.3fr 1fr"],
  [style*="grid-template-columns:1fr 2fr"],[style*="grid-template-columns:1fr 340px"],
  [style*="grid-template-columns:1fr 60px 1fr"]{grid-template-columns:1fr!important;gap:28px!important}
  [style*="grid-template-columns:repeat(3,1fr)"],[style*="grid-template-columns:repeat(4,1fr)"]{grid-template-columns:1fr 1fr!important;gap:12px!important}
  [style*="position:sticky"]{position:relative!important;top:0!important}
  #hero{min-height:85vh!important}
  #hero h1{font-size:clamp(36px,7vw,58px)!important}
}
/* ─ 스마트폰 (≤600px) ─ */
@media(max-width:600px){
  .sec{padding:36px 16px}
  .sec-h2{font-size:clamp(22px,5.5vw,30px)!important}
  [style*="grid-template-columns"]{grid-template-columns:1fr!important;gap:10px!important}
  .btn-p{width:100%!important;justify-content:center!important;font-size:15px!important;padding:16px 20px!important}
  [style*="display:flex;gap:12px"],[style*="display:flex;gap:14px"]{flex-direction:column!important;align-items:stretch!important}
  #hero{padding:clamp(56px,12vw,72px) 16px clamp(36px,8vw,52px)!important;min-height:90vh!important}
  #hero h1{font-size:clamp(30px,8vw,50px)!important}
  .card{padding:16px!important}
  details summary{padding:13px 14px!important;font-size:13px!important}
  .card[style*="grid-column:1 / -1"]{display:flex!important;flex-direction:column!important}
  [style*="display:flex;gap:36px"]{flex-wrap:wrap!important;gap:18px!important}
  [style*="text-align:center"] h2{font-size:clamp(22px,6vw,34px)!important}
  #cdtimer{gap:8px!important}
  #cdtimer>div{min-width:52px!important;padding:9px 10px!important}
  #cdtimer>div>div:first-child{font-size:26px!important}
}
/* ─ 초소형 (≤380px) ─ */
@media(max-width:380px){
  .sec{padding:28px 12px}
  #hero h1{font-size:clamp(26px,9vw,38px)!important}
}
/* ─ 모바일 플로팅 CTA (★ v7.5) ─ */
.mob-cta{display:none}
@media(max-width:600px){
  .mob-cta{display:flex;position:fixed;bottom:0;left:0;right:0;z-index:9999;
    padding:12px 16px calc(12px + env(safe-area-inset-bottom));
    background:rgba(10,10,10,.96);backdrop-filter:blur(14px);
    border-top:1px solid rgba(255,255,255,.1);gap:10px;align-items:center}
  .mob-cta a:first-child{flex:1;display:flex;align-items:center;justify-content:center;
    background:var(--c1);color:#fff;font-weight:800;font-size:15px;
    padding:14px 20px;border-radius:var(--r-btn,4px);text-decoration:none}
  .mob-cta a:last-child{flex-shrink:0;display:flex;align-items:center;justify-content:center;
    background:rgba(255,255,255,.08);color:rgba(255,255,255,.7);font-size:13px;font-weight:600;
    padding:13px 16px;border-radius:var(--r-btn,4px);border:1px solid rgba(255,255,255,.2);text-decoration:none}
  body{padding-bottom:72px}
}
"""

def _particle_js(particle:str)->str:
    if particle=="snow": return """<style>.sf{position:fixed;top:-20px;color:#fff;font-size:1.2em;text-shadow:0 0 8px rgba(180,220,255,.8);animation:sfall linear infinite;pointer-events:none;z-index:9999;opacity:.8}@keyframes sfall{0%{transform:translateY(-20px) rotate(0deg);opacity:.8}100%{transform:translateY(110vh) rotate(360deg);opacity:0}}</style><script>(function(){var c=["❄","❅","❆","✦","·"];for(var i=0;i<25;i++){var el=document.createElement("span");el.className="sf";el.textContent=c[Math.floor(Math.random()*c.length)];el.style.cssText="left:"+Math.random()*100+"vw;font-size:"+(0.8+Math.random()*1.6)+"em;animation-duration:"+(4+Math.random()*8)+"s;animation-delay:"+(-Math.random()*8)+"s;opacity:"+(0.4+Math.random()*.6);document.body.appendChild(el);}})()</script>"""
    if particle=="stars": return """<style>.sp{position:fixed;border-radius:50%;background:#fff;animation:twinkle ease-in-out infinite;pointer-events:none;z-index:9999}@keyframes twinkle{0%,100%{opacity:.1;transform:scale(1)}50%{opacity:1;transform:scale(1.5)}}</style><script>(function(){for(var i=0;i<70;i++){var el=document.createElement("div");el.className="sp";var s=1+Math.random()*2.5;el.style.cssText="width:"+s+"px;height:"+s+"px;top:"+Math.random()*100+"vh;left:"+Math.random()*100+"vw;animation-duration:"+(1.5+Math.random()*3)+"s;animation-delay:"+(-Math.random()*3)+"s;box-shadow:0 0 "+(s*2)+"px rgba(180,200,255,.9)";document.body.appendChild(el);}})()</script>"""
    if particle=="petals": return """<style>.pt{position:fixed;top:-20px;font-size:1.1em;animation:pfall linear infinite;pointer-events:none;z-index:9999;opacity:.7}@keyframes pfall{0%{transform:translateY(-20px) rotate(0deg) translateX(0);opacity:.7}50%{transform:translateY(55vh) rotate(180deg) translateX(30px);opacity:.5}100%{transform:translateY(110vh) rotate(360deg) translateX(-10px);opacity:0}}</style><script>(function(){var p=["🌸","🌺","🌼","✿","❀"];for(var i=0;i<20;i++){var el=document.createElement("span");el.className="pt";el.textContent=p[Math.floor(Math.random()*p.length)];el.style.cssText="left:"+Math.random()*100+"vw;font-size:"+(0.7+Math.random()*1.2)+"em;animation-duration:"+(5+Math.random()*8)+"s;animation-delay:"+(-Math.random()*8)+"s";document.body.appendChild(el);}})()</script>"""
    if particle=="embers": return """<style>.em{position:fixed;bottom:-10px;border-radius:50%;animation:erise linear infinite;pointer-events:none;z-index:9999}@keyframes erise{0%{transform:translateY(0) translateX(0) scale(1);opacity:.9}50%{transform:translateY(-45vh) translateX(20px) scale(.7);opacity:.6}100%{transform:translateY(-95vh) translateX(-10px) scale(.2);opacity:0}}</style><script>(function(){var c=["#FF4500","#FF8C00","#FFD700","#FF6347"];for(var i=0;i<30;i++){var el=document.createElement("div");el.className="em";var s=2+Math.random()*4;el.style.cssText="width:"+s+"px;height:"+s+"px;left:"+Math.random()*100+"vw;background:"+c[Math.floor(Math.random()*c.length)]+";box-shadow:0 0 "+s+"px #FF4500;animation-duration:"+(3+Math.random()*5)+"s;animation-delay:"+(-Math.random()*5)+"s";document.body.appendChild(el);}})()</script>"""
    if particle=="gold": return """<style>.gp{position:fixed;top:-10px;font-size:.9em;animation:gfall linear infinite;pointer-events:none;z-index:9999}@keyframes gfall{0%{transform:translateY(-20px) rotate(0deg);opacity:.9}100%{transform:translateY(110vh) rotate(720deg);opacity:0}}</style><script>(function(){var g=["✦","★","◆","·","⬥"];for(var i=0;i<35;i++){var el=document.createElement("span");el.className="gp";el.textContent=g[Math.floor(Math.random()*g.length)];el.style.cssText="left:"+Math.random()*100+"vw;color:"+["#FFD700","#C8975A","#F5C842","#FFA500"][Math.floor(Math.random()*4)]+";font-size:"+(0.5+Math.random()*1)+"em;animation-duration:"+(4+Math.random()*6)+"s;animation-delay:"+(-Math.random()*6)+"s;text-shadow:0 0 8px #FFD700";document.body.appendChild(el);}})()</script>"""
    if particle=="leaves": return """<style>.lf{position:fixed;top:-20px;font-size:1em;animation:lfall linear infinite;pointer-events:none;z-index:9999}@keyframes lfall{0%{transform:translateY(-20px) rotate(0deg) translateX(0);opacity:.8}100%{transform:translateY(110vh) rotate(540deg) translateX(40px);opacity:0}}</style><script>(function(){var l=["🍃","🍂","🍁","🌿","🌾"];for(var i=0;i<18;i++){var el=document.createElement("span");el.className="lf";el.textContent=l[Math.floor(Math.random()*l.length)];el.style.cssText="left:"+Math.random()*100+"vw;font-size:"+(0.8+Math.random()*1.2)+"em;animation-duration:"+(5+Math.random()*7)+"s;animation-delay:"+(-Math.random()*7)+"s";document.body.appendChild(el);}})()</script>"""
    return ""


# ══════════════════════════════════════════════════════
# 섹션 빌더
# ══════════════════════════════════════════════════════
def _bg_vars(bg_url,dark):
    if not bg_url:
        return {"hero_bg":"background:var(--bg)","overlay":"","tc":"color:var(--text)",
                "t70c":"color:var(--t70)","c1c":"var(--c1)","bdc":"var(--bd)","blur":""}
    return {"hero_bg":f"background:var(--bg) url('{bg_url}') center/cover no-repeat",
            "overlay":'<div style="position:absolute;inset:0;background:rgba(0,0,0,.62);z-index:1;pointer-events:none"></div>',
            "tc":"color:#fff","t70c":"color:rgba(255,255,255,.82)","c1c":"#fff",
            "bdc":"rgba(255,255,255,.28)","blur":"backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);"}

def sec_banner(d,cp,T):
    sub=strip_hanja(cp.get("bannerSub",d["subject"]+" 완성"))
    title=strip_hanja(cp.get("bannerTitle",d["purpose_label"]))
    lead=strip_hanja(cp.get("bannerLead",f"{d['target']}을 위한 커리큘럼"))
    tagline=strip_hanja(cp.get("brandTagline",""))
    cta=strip_hanja(cp.get("ctaCopy","수강신청하기"))
    kws=SUBJ_KW.get(d["subject"],["개념","기출","실전","파이널"])
    bg_url=cp.get("bg_photo_url","")
    hs=T.get("heroStyle","typographic"); s=_bg_vars(bg_url,T["dark"]); dark=T["dark"]
    kh="".join(f'<span style="font-size:9px;font-weight:800;padding:5px 14px;border-radius:var(--r-btn,4px);color:{s["c1c"]};border:1px solid {s["bdc"]};margin:2px;letter-spacing:.1em">{k}</span>' for k in kws)
    text_col="#fff" if (dark or bg_url) else "var(--text)"
    t70_col="rgba(255,255,255,.72)" if (dark or bg_url) else "var(--t70)"
    accent_col=s["c1c"] if bg_url else "var(--c1)"
    bd_c=s["bdc"] if bg_url else "var(--bd)"
    blur_=s.get("blur","") if bg_url else "backdrop-filter:blur(8px)"

    if hs=="typographic":
        deco=title[:3] if title else sub[:3]
        return (f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:flex;flex-direction:column;justify-content:flex-end">'+s["overlay"]+
                f'<div style="position:absolute;top:0;left:0;right:0;bottom:0;background:linear-gradient(to top,rgba(0,0,0,.92) 0%,rgba(0,0,0,.2) 50%,transparent 100%);z-index:1;pointer-events:none"></div>'+
                f'<div style="position:absolute;top:-0.05em;right:-0.05em;font-family:var(--fh);font-size:38vw;font-weight:900;line-height:0.85;color:var(--c1);opacity:.04;pointer-events:none;z-index:1;user-select:none;overflow:hidden">{deco}</div>'+
                f'<div style="position:relative;z-index:2;padding:clamp(60px,8vw,100px) clamp(22px,6vw,80px);max-width:min(1000px,100%)">'
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:24px"><div style="width:36px;height:3px;background:{accent_col}"></div><span style="font-size:9.5px;font-weight:800;letter-spacing:.22em;text-transform:uppercase;color:{accent_col}">{sub}</span></div>'
                f'<h1 style="font-family:var(--fh);font-size:clamp(38px,7vw,108px);font-weight:900;line-height:.9;letter-spacing:-.04em;word-break:keep-all;color:{text_col};margin-bottom:20px" class="st">{title}</h1>'
                +(f'<div style="font-size:clamp(13px,1.7vw,19px);font-style:italic;font-weight:300;color:{accent_col};margin-bottom:16px;line-height:1.5;opacity:.9">{tagline}</div>' if tagline else "")
                +f'<div style="width:100%;height:1px;background:linear-gradient(to right,{accent_col},transparent);margin-bottom:22px;opacity:.35"></div>'
                f'<p style="font-size:clamp(13px,1.6vw,16px);line-height:1.9;color:{t70_col};max-width:520px;padding-left:18px;border-left:3px solid {accent_col};margin-bottom:24px">{lead}</p>'
                f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:24px">{kh}</div>'
                f'<div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:20px">'
                f'<a class="btn-p" href="#" style="font-size:15px;padding:16px 40px">{cta} →</a>'
                f'<a href="#" style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.08);{blur_};color:{text_col};font-weight:600;padding:15px 26px;border-radius:var(--r-btn,4px);border:1.5px solid {bd_c};font-size:14px;text-decoration:none">강의 미리보기 ↗</a>'
                f'</div></div></section>')

    elif hs=="cinematic":
        return (f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:flex;flex-direction:column;justify-content:flex-end">'+s["overlay"]+
                f'<div style="position:absolute;inset:0;background:linear-gradient(160deg,transparent 30%,rgba(0,0,0,.85) 100%);z-index:1;pointer-events:none"></div>'
                f'<div style="position:absolute;top:0;left:0;right:0;height:6px;background:var(--c1);z-index:3"></div>'
                f'<div style="position:absolute;bottom:0;left:0;right:0;height:6px;background:var(--c1);z-index:3"></div>'
                f'<div style="position:relative;z-index:2;padding:80px clamp(22px,6vw,80px) 80px">'
                f'<div style="display:inline-flex;align-items:center;gap:10px;margin-bottom:22px;padding:5px 16px;border:1.5px solid var(--c1);border-radius:2px">'
                f'<div style="width:8px;height:8px;background:var(--c1);border-radius:50%;animation:pulse-accent 1.5s ease-in-out infinite"></div>'
                f'<span style="font-size:10px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:var(--c1)">{sub}</span></div>'
                f'<h1 style="font-family:var(--fh);font-size:clamp(34px,6.5vw,96px);font-weight:900;line-height:.92;letter-spacing:-.04em;word-break:keep-all;color:#fff;margin-bottom:16px" class="st">{title}</h1>'
                +(f'<div style="font-size:clamp(13px,1.6vw,18px);font-style:italic;font-weight:300;color:var(--c1);margin-bottom:16px;line-height:1.5;opacity:.9">{tagline}</div>' if tagline else "")
                +f'<p style="font-size:14px;line-height:2;color:rgba(255,255,255,.72);max-width:480px;border-left:3px solid var(--c1);padding-left:18px;margin-bottom:28px">{lead}</p>'
                f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:24px">{kh}</div>'
                f'<div style="display:flex;gap:12px;flex-wrap:wrap"><a class="btn-p" href="#" style="font-size:15px;padding:16px 44px">{cta} →</a></div>'
                f'</div></section>')

    elif hs=="billboard":
        parts=title.split(); l1=parts[0] if parts else title; l2=" ".join(parts[1:]) if len(parts)>1 else ""
        return (f'<section id="hero" style="min-height:100vh;background:var(--bg);position:relative;overflow:hidden;display:flex;flex-direction:column;justify-content:center;padding:80px clamp(22px,7vw,100px)">'
                f'<div style="position:absolute;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 79px,var(--bd) 79px,var(--bd) 80px);opacity:.25;pointer-events:none"></div>'
                f'<div style="position:relative;z-index:1">'
                f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:28px"><div style="width:48px;height:4px;background:var(--c1)"></div><span style="font-size:9.5px;font-weight:800;letter-spacing:.22em;text-transform:uppercase;color:var(--c1)">{sub}</span></div>'
                f'<div style="font-family:var(--fh);font-size:clamp(44px,9vw,140px);font-weight:900;line-height:.88;letter-spacing:-.05em;word-break:keep-all;color:var(--text)" class="st">{l1}</div>'
                +(f'<div style="font-family:var(--fh);font-size:clamp(44px,9vw,140px);font-weight:900;line-height:.88;letter-spacing:-.05em;color:transparent;-webkit-text-stroke:2px var(--c1)">{l2}</div>' if l2 else "")
                +f'<div style="display:flex;align-items:center;gap:28px;margin-top:36px;padding-top:28px;border-top:2px solid var(--c1);flex-wrap:wrap">'
                f'<p style="font-size:14px;line-height:1.9;color:var(--t70);max-width:380px">{lead}</p>'
                f'<a class="btn-p" href="#" style="flex-shrink:0;font-size:15px;padding:16px 44px">{cta} →</a>'
                f'</div></div></section>')

    elif hs=="editorial_bold":
        return (f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:grid;grid-template-rows:auto 1fr auto">'+s["overlay"]+
                f'<div style="position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,.2) 0%,rgba(0,0,0,.75) 100%);z-index:1;pointer-events:none"></div>'
                f'<div style="position:relative;z-index:2;padding:26px clamp(22px,5vw,80px);display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid {bd_c};flex-wrap:wrap;gap:10px">'
                f'<div style="font-family:var(--fh);font-size:14px;font-weight:900;color:{text_col};letter-spacing:.06em">{d["subject"].upper()} · {d["name"] if d["name"] else "강사"}</div>'
                f'<div style="display:flex;gap:5px;flex-wrap:wrap">{kh}</div></div>'
                f'<div style="position:relative;z-index:2;padding:clamp(38px,6vw,76px) clamp(22px,5vw,80px);display:flex;flex-direction:column;justify-content:center">'
                f'<div style="font-size:10px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:{accent_col};margin-bottom:18px">{sub}</div>'
                f'<h1 style="font-family:var(--fh);font-size:clamp(32px,5.5vw,80px);font-weight:900;line-height:.95;letter-spacing:-.04em;word-break:keep-all;color:{text_col};max-width:800px;margin-bottom:16px" class="st">{title}</h1>'
                +(f'<div style="font-size:clamp(13px,1.5vw,18px);font-style:italic;font-weight:300;color:{accent_col};margin-bottom:18px;line-height:1.5;opacity:.9">{tagline}</div>' if tagline else "")
                +f'<div style="display:flex;gap:36px;align-items:flex-start;flex-wrap:wrap">'
                f'<p style="font-size:clamp(13px,1.4vw,16px);line-height:1.95;color:{t70_col};max-width:420px;padding-left:18px;border-left:3px solid {accent_col}">{lead}</p>'
                f'<a class="btn-p" href="#" style="flex-shrink:0;font-size:15px;padding:16px 44px">{cta} →</a>'
                f'</div></div>'
                f'<div style="position:relative;z-index:2;padding:22px clamp(22px,5vw,80px);border-top:1px solid {bd_c}"></div>'
                f'</section>')

    elif hs=="split_bold":
        return (f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:grid;grid-template-columns:1fr 1fr">'+s["overlay"]+
                f'<div style="position:relative;z-index:2;display:flex;flex-direction:column;justify-content:center;padding:clamp(56px,7vw,100px) clamp(22px,5vw,56px)">'
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:22px"><div style="width:36px;height:3px;background:{accent_col}"></div><span style="font-size:9px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:{accent_col}">{sub}</span></div>'
                f'<h1 style="font-family:var(--fh);font-size:clamp(32px,5.5vw,72px);font-weight:900;line-height:.9;letter-spacing:-.04em;color:{text_col};margin-bottom:18px" class="st">{title}</h1>'
                f'<p style="font-size:14px;line-height:2;color:{t70_col};max-width:380px;margin-bottom:26px">{lead}</p>'
                f'<a class="btn-p" href="#" style="align-self:flex-start;font-size:14px;padding:14px 36px">{cta} →</a>'
                f'</div>'
                f'<div style="position:relative;z-index:2;background:var(--c1);display:flex;align-items:center;justify-content:center;padding:48px 32px">'
                f'<div style="width:100%;max-width:320px">'
                f'<div style="font-size:11px;font-weight:800;letter-spacing:.15em;text-transform:uppercase;color:rgba(0,0,0,.5);margin-bottom:18px">{d["purpose_label"][:14]}</div>'
                f'<div style="font-family:var(--fh);font-size:clamp(28px,3vw,46px);font-weight:900;color:#fff;line-height:1.05;margin-bottom:18px">{title}</div>'
                f'<a style="display:flex;align-items:center;justify-content:center;gap:8px;background:#fff;color:var(--c1);font-weight:800;font-size:14px;padding:14px;border-radius:var(--r-btn,4px);margin-top:18px;text-decoration:none">{cta} →</a>'
                f'</div></div></section>')

    else:  # immersive/split/default
        return (f'<section id="hero" style="position:relative;min-height:100vh;overflow:hidden;{s["hero_bg"]};display:flex;flex-direction:column;justify-content:flex-end">'+s["overlay"]+
                f'<div style="position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.9) 0%,rgba(0,0,0,.1) 60%,transparent 100%);z-index:1;pointer-events:none"></div>'
                f'<div style="position:relative;z-index:2;padding:clamp(46px,6vw,80px) clamp(22px,5vw,80px);max-width:900px">'
                f'<div style="display:inline-flex;align-items:center;gap:9px;background:rgba(255,255,255,.12);{s.get("blur","")};padding:6px 16px;border-radius:100px;margin-bottom:20px;border:1px solid rgba(255,255,255,.2)">'
                f'<span style="font-size:10px;font-weight:800;color:#fff;letter-spacing:.14em;text-transform:uppercase">{sub}</span></div>'
                f'<h1 style="font-family:var(--fh);font-size:clamp(32px,5vw,80px);font-weight:900;line-height:.95;letter-spacing:-.04em;word-break:keep-all;color:#fff;margin-bottom:18px" class="st">{title}</h1>'
                f'<p style="font-size:clamp(13px,1.5vw,16px);line-height:1.9;color:rgba(255,255,255,.78);max-width:500px;margin-bottom:26px;padding-left:16px;border-left:3px solid #fff">{lead}</p>'
                f'<div style="display:flex;gap:12px;flex-wrap:wrap"><a class="btn-p" href="#" style="font-size:15px;padding:16px 44px">{cta} →</a></div>'
                f'</div></section>')


def sec_intro(d,cp,T):
    ip=st.session_state.get("inst_profile") or {}
    t=strip_hanja(cp.get("introTitle",f"{d['name']} 선생님 소개" if d["name"] else f"{d['subject']} 강사 소개"))
    desc=strip_hanja(cp.get("introDesc",f"{d['subject']} 최상위권 합격의 비결"))
    bio=strip_hanja(cp.get("introBio",ip.get("desc",f"검증된 {d['subject']} 강사")))
    methods=[strip_hanja(m) for m in (ip.get("signatureMethods") or []) if m and m not in ("없음","")]
    slogan=strip_hanja(ip.get("slogan",""))
    mtags="".join(f'<div style="display:flex;align-items:center;gap:10px;padding:11px 14px;border:1.5px solid var(--c1);border-radius:var(--r,4px);margin-bottom:8px"><div style="width:6px;height:6px;border-radius:50%;background:var(--c1);flex-shrink:0"></div><span style="font-size:13px;font-weight:800;color:var(--text)">{m}</span></div>' for m in methods[:4]) if methods else f'<div style="font-size:13px;color:var(--t45)">{d["subject"]} 전문 강의</div>'
    slogan_html=(f'<div class="rv d1" style="padding:26px 28px;background:var(--bg3);border-radius:var(--r,4px);position:relative;overflow:hidden;margin-top:22px"><div style="position:absolute;top:-12px;left:10px;font-family:var(--fh);font-size:100px;font-weight:900;color:var(--c1);opacity:.06;line-height:1">"</div><p style="font-size:clamp(13px,1.4vw,16px);line-height:1.9;font-style:italic;color:var(--text);font-weight:500;position:relative;z-index:1;padding-top:8px">{slogan}</p><div style="display:flex;align-items:center;gap:8px;margin-top:12px"><div style="width:24px;height:2px;background:var(--c1)"></div><span style="font-size:10px;font-weight:800;color:var(--c1);letter-spacing:.12em;text-transform:uppercase">{d["name"] if d["name"] else "강사"} 선생님</span></div></div>') if slogan else ""
    return (f'<section class="sec alt" id="intro"><div style="max-width:1200px;margin:0 auto"><div class="rv" style="display:grid;grid-template-columns:1fr auto;align-items:flex-end;gap:20px;padding-bottom:22px;border-bottom:2px solid var(--c1);margin-bottom:40px"><div><div class="tag-line">강사 소개</div><h2 class="sec-h2 st" style="margin-bottom:0">{t}</h2></div><div style="text-align:right"><div style="font-size:10px;font-weight:800;letter-spacing:.14em;color:var(--t45);text-transform:uppercase;margin-bottom:4px">{d["subject"]}</div><div style="font-family:var(--fh);font-size:19px;font-weight:900;color:var(--c1)">{d["purpose_label"][:14]}</div></div></div>'
             f'<div style="display:grid;grid-template-columns:1.3fr 1fr 0.85fr;gap:36px;align-items:start">'
             f'<div class="rv d1"><p style="font-size:15px;line-height:2;color:var(--t70)">{desc}</p>{slogan_html}</div>'
             f'<div class="rv d2" style="padding-left:24px;border-left:3px solid var(--bd)"><div style="font-size:10px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--c1);margin-bottom:12px">PROFILE</div><p style="font-size:13.5px;line-height:2;color:var(--text)">{bio}</p></div>'
             f'<div class="rv d3"><div style="font-size:10px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--c1);margin-bottom:12px">SIGNATURE</div>{mtags}</div>'
             f'</div></div></section>')

def sec_why(d,cp,T):
    t=strip_hanja(cp.get("whyTitle","이 강의가 필요한 이유"))
    s=strip_hanja(cp.get("whySub",f"{d['subject']} 1등급의 비결"))
    reasons=cp.get("whyReasons",[["🎯","유형별 완전 정복","수능 출제 유형을 완전히 분석하여 어떤 문제도 흔들리지 않는 실력을 만듭니다."],["📊","기출 데이터 분석","최근 5년 기출을 철저히 분석하여 실전에서 반드시 나오는 유형만 집중 훈련합니다."],["⚡","실전 속도 훈련","정확도와 속도를 동시에 잡아 70분 안에 45문항을 완벽히 소화하는 훈련을 합니다."]])
    safe_r=[]
    for item in reasons:
        if isinstance(item,(list,tuple)) and len(item)>=3: safe_r.append((str(item[0]),str(item[1]),str(item[2])))
        elif isinstance(item,dict): safe_r.append((item.get("icon","✦"),item.get("title",""),item.get("desc","")))
    rh="".join(f'<div class="rv d{i}" style="display:grid;grid-template-columns:90px 1fr;gap:0;align-items:stretch;border:1px solid var(--bd);border-radius:var(--r,4px);overflow:hidden;margin-bottom:10px"><div style="display:flex;flex-direction:column;align-items:center;justify-content:center;{"background:var(--bg3)" if i%2==0 else "background:var(--bg)"};padding:18px 10px;border-right:1px solid var(--bd)"><div style="font-family:var(--fh);font-size:40px;font-weight:900;line-height:1;color:var(--c1);opacity:.2">{i:02d}</div><div style="font-size:24px;margin-top:7px">{ic}</div></div><div style="padding:18px 22px;display:flex;flex-direction:column;justify-content:center"><div style="font-family:var(--fh);font-size:clamp(14px,1.5vw,17px);font-weight:800;margin-bottom:7px;letter-spacing:-.02em;color:var(--text)" class="st">{strip_hanja(tt)}</div><p style="font-size:13px;line-height:1.9;color:var(--t70);margin:0">{strip_hanja(dc)}</p></div></div>' for i,(ic,tt,dc) in enumerate(safe_r,1))
    return (f'<section class="sec" id="why"><div style="display:grid;grid-template-columns:1fr 1.6fr;gap:72px;align-items:start;max-width:1200px;margin:0 auto"><div class="rv" style="position:sticky;top:60px"><div class="tag-line">수강 이유</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{s}</p><div style="margin-top:22px;padding:18px 22px;background:var(--c1);border-radius:var(--r,4px)"><div style="font-family:var(--fh);font-size:38px;font-weight:900;color:#fff;line-height:1">{len(safe_r)}</div><div style="font-size:11px;color:rgba(255,255,255,.7);margin-top:3px;font-weight:700">가지 핵심 이유</div></div></div><div class="rv d1">{rh}</div></div></section>')

def sec_curriculum(d,cp,T):
    t=strip_hanja(cp.get("curriculumTitle",f"{d['purpose_label']} 커리큘럼"))
    s=strip_hanja(cp.get("curriculumSub","4단계 완성 로드맵"))
    steps=cp.get("curriculumSteps",[["01","개념 완성","핵심 개념과 공식, 왜 이 단계가 필요한지 이해합니다.","4주"],["02","유형 훈련","기출 완전 분석으로 실전 패턴을 파악합니다.","4주"],["03","심화 특훈","고난도 아이디어를 완전히 내 것으로 만듭니다.","3주"],["04","파이널","실수 제거와 시간 배분으로 실전을 완성합니다.","3주"]])
    sh="".join(f'<div class="rv d{min(idx+1,4)}" style="display:flex;gap:18px;align-items:flex-start;padding-bottom:{"0" if idx==len(steps)-1 else "24px"};{"" if idx==len(steps)-1 else "border-bottom:1px solid var(--bd)"};margin-bottom:{"0" if idx==len(steps)-1 else "24px"}"><div style="flex-shrink:0;width:50px;height:50px;border-radius:var(--r,4px);background:var(--c1);display:flex;align-items:center;justify-content:center;font-family:var(--fh);font-size:13px;font-weight:900;color:#fff">0{idx+1}</div><div style="flex:1"><div style="display:flex;align-items:center;gap:10px;margin-bottom:5px;flex-wrap:wrap"><div style="font-family:var(--fh);font-size:15px;font-weight:700;letter-spacing:-.02em" class="st">{strip_hanja(str(step[1]))}</div><span style="font-size:9px;background:var(--bg3);color:var(--c1);padding:3px 10px;border-radius:100px;font-weight:700;border:1px solid var(--bd)">{step[3] if len(step)>3 else "4주"}</span></div><p style="font-size:13px;line-height:1.8;color:var(--t70)">{strip_hanja(str(step[2]))}</p></div></div>' for idx,step in enumerate(steps))
    return (f'<section class="sec alt" id="curriculum"><div style="display:grid;grid-template-columns:1fr 1.4fr;gap:72px;align-items:start;max-width:1200px;margin:0 auto"><div class="rv" style="position:sticky;top:60px"><div class="tag-line">커리큘럼</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{s}</p><div style="padding:18px 22px;background:var(--c1);border-radius:var(--r,4px);margin-top:6px"><div style="font-size:10px;font-weight:800;letter-spacing:.15em;text-transform:uppercase;color:rgba(255,255,255,.6);margin-bottom:7px">TOTAL</div><div style="font-family:var(--fh);font-size:34px;font-weight:900;color:#fff">{len(steps)*4}주</div><div style="font-size:11px;color:rgba(255,255,255,.7);margin-top:3px">{len(steps)}단계 완성 과정</div></div></div><div>{sh}</div></div></section>')

def sec_target(d,cp,T):
    t=strip_hanja(cp.get("targetTitle","이런 분들께 추천합니다"))
    items=[strip_hanja(str(it)) for it in cp.get("targetItems",[f"수능까지 {d['subject']} 점수를 확실히 올리고 싶은 분","개념은 아는데 실전에서 점수가 안 나오는 분","N수를 준비하며 체계적인 커리큘럼이 필요한 분",f"{d['subject']} 상위권 도약을 원하는 분"])]
    def card(i,txt): return f'<div class="rv d{min(i+1,4)}" style="padding:18px 22px;border:1px solid var(--bd);border-radius:var(--r,4px);background:var(--bg);margin-bottom:10px;display:flex;gap:12px;align-items:flex-start"><div style="flex-shrink:0;width:32px;height:32px;border-radius:var(--r-btn,4px);background:var(--c1);display:flex;align-items:center;justify-content:center;font-family:var(--fh);font-size:12px;font-weight:900;color:#fff">{i+1:02d}</div><p style="font-size:14px;font-weight:600;line-height:1.7;color:var(--text);margin:0">{txt}</p></div>'
    lh="".join(card(i,txt) for i,txt in [(i,t) for i,t in enumerate(items) if i%2==0])
    rh="".join(card(i,txt) for i,txt in [(i,t) for i,t in enumerate(items) if i%2==1])
    return (f'<section class="sec" id="target"><div style="max-width:1200px;margin:0 auto"><div class="rv" style="display:grid;grid-template-columns:1fr 2fr;gap:56px;align-items:start"><div style="position:sticky;top:60px"><div class="tag-line">수강 대상</div><h2 class="sec-h2 st">{t}</h2></div><div style="display:grid;grid-template-columns:1fr 1fr;gap:0 18px"><div>{lh}</div><div style="padding-top:52px">{rh}</div></div></div></div></section>')

def sec_reviews(d,cp,T):
    reviews=cp.get("reviews",[[f'"개념이 이렇게 명확하게 보인 적이 없었어요. {d["subject"]} 공부가 달라졌습니다."',f"고3 김OO","등급 향상"],["\"3주 만에 독해 속도가 확실히 빨라졌어요.\"","N수 이OO","실전 완성"],[f'"선생님 덕분에 {d["subject"]} 구조가 보이기 시작했어요."',"고2 박OO","자신감 회복"]])
    rh=""
    for i,(txt,nm,badge) in enumerate(reviews):
        if i==0:
            rh+=(f'<div class="card rv d1" style="grid-column:1 / -1;display:grid;grid-template-columns:1fr 1fr;gap:0;overflow:hidden;border-radius:var(--r,4px)"><div style="background:var(--c1);padding:32px;display:flex;flex-direction:column;justify-content:space-between"><div style="font-family:var(--fh);font-size:64px;font-weight:900;color:rgba(255,255,255,.15);line-height:.8;margin-bottom:10px">"</div><p style="font-size:clamp(13px,1.4vw,17px);line-height:1.85;font-weight:600;color:#fff;flex:1">{strip_hanja(txt)}</p><div style="margin-top:18px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px"><span style="font-size:12px;font-weight:700;color:rgba(255,255,255,.75)">— {nm} 학생</span><span style="font-size:10px;background:rgba(255,255,255,.18);color:#fff;padding:4px 14px;border-radius:var(--r-btn,100px);font-weight:800">{badge}</span></div></div><div style="background:var(--bg3);padding:32px;display:flex;flex-direction:column;justify-content:center"><div style="display:flex;gap:3px;color:#F59E0B;font-size:18px;margin-bottom:14px">{"★"*5}</div><div style="font-size:10px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--c1);margin-bottom:8px">BEST REVIEW</div><p style="font-size:13px;line-height:1.9;color:var(--t70)">이 수강생의 변화는 {d["subject"]} 공부 방식 자체가 달라진 결과입니다.</p></div></div>')
        else:
            rh+=(f'<div class="card rv d{i+1}" style="display:flex;flex-direction:column;gap:12px;padding:22px"><div style="display:flex;gap:2px;color:#F59E0B;font-size:12px">{"★"*5}</div><p style="font-size:13.5px;line-height:1.9;font-weight:500;flex:1">{strip_hanja(txt)}</p><div style="display:flex;align-items:center;justify-content:space-between;padding-top:10px;border-top:1px solid var(--bd);flex-wrap:wrap;gap:6px"><span style="font-size:11px;color:var(--t45)">— {nm} 학생</span><span style="font-size:9.5px;background:var(--bg3);color:var(--c1);padding:3px 12px;border-radius:var(--r-btn,100px);font-weight:700;border:1px solid var(--bd)">{badge}</span></div></div>')
    return (f'<section class="sec alt" id="reviews"><div style="max-width:1200px;margin:0 auto"><div class="rv" style="margin-bottom:36px"><div class="tag-line">수강평</div><h2 class="sec-h2 st">생생한 수강생 후기</h2></div><div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px">{rh}</div></div></section>')

def sec_faq(d,cp,T):
    raw=cp.get("faqs",[["수강 기간은 얼마나 되나요?","기본 30일이며 연장권 구매 시 최대 90일까지 연장 가능합니다."],["교재는 별도 구매인가요?","별도 구매입니다. 수강 신청 페이지에서 패키지로 구매 시 할인 혜택이 적용됩니다."],["모바일에서도 수강 가능한가요?","PC, 태블릿, 스마트폰 모두 지원합니다. 앱에서 오프라인 다운로드도 가능합니다."]])
    faqs=[]
    for item in raw:
        if isinstance(item,dict): faqs.append([item.get("question",item.get("q","")),item.get("answer",item.get("a",""))])
        elif isinstance(item,list) and len(item)>=2: faqs.append([str(item[0]),str(item[1])])
    fh="".join(f'<div class="rv d{min(i+1,3)}" style="margin-bottom:6px"><details style="border:1px solid var(--bd);border-radius:var(--r,4px);overflow:hidden"><summary style="padding:15px 20px;background:var(--bg3);display:flex;align-items:center;gap:12px;cursor:pointer;list-style:none;user-select:none"><span style="color:var(--c1);font-weight:900;font-size:14px;flex-shrink:0;font-family:var(--fh)">Q.</span><span style="font-weight:700;font-size:14px;line-height:1.5;flex:1">{strip_hanja(q)}</span><span style="font-size:18px;color:var(--c1);flex-shrink:0">＋</span></summary><div style="padding:16px 20px;background:var(--bg);display:flex;gap:10px;align-items:flex-start;border-top:1px solid var(--bd)"><span style="color:var(--t45);font-weight:700;font-size:14px;flex-shrink:0">A.</span><p style="font-size:13.5px;line-height:1.9;color:var(--t70);margin:0">{strip_hanja(a)}</p></div></details></div>' for i,(q,a) in enumerate(faqs))
    return (f'<section class="sec" id="faq"><div style="display:grid;grid-template-columns:1fr 1.8fr;gap:72px;align-items:start;max-width:1200px;margin:0 auto"><div class="rv" style="position:sticky;top:60px"><div class="tag-line">FAQ</div><h2 class="sec-h2 st">자주 묻는 질문</h2><p class="sec-sub">궁금한 점을 클릭해 답변을 확인하세요.</p></div><div class="rv d1">{fh}</div></div></section>')

def sec_cta(d,cp,T):
    tt=strip_hanja(cp.get("ctaTitle",f"지금 바로 시작해<br>{d['subject']} 1등급을 확보하세요"))
    sub=strip_hanja(cp.get("ctaSub",f"{d['name']} 선생님과 함께라면 가능합니다." if d["name"] else f"{d['subject']} 1등급, 지금 시작하세요."))
    cc=strip_hanja(cp.get("ctaCopy","지금 수강신청하기")); badge=strip_hanja(cp.get("ctaBadge",f"{d['target']} 전용"))
    return (f'<section style="padding:clamp(64px,10vw,108px) clamp(22px,5vw,72px);text-align:center;position:relative;overflow:hidden;background:{T["cta"]}"><div style="position:absolute;top:-100px;right:-100px;width:400px;height:400px;border-radius:50%;background:rgba(255,255,255,.03);pointer-events:none"></div><div style="position:relative;z-index:1"><div style="display:inline-block;background:rgba(255,255,255,.12);padding:6px 18px;border-radius:100px;font-size:10px;font-weight:800;color:#fff;margin-bottom:20px;letter-spacing:.14em;text-transform:uppercase">{badge}</div><h2 style="font-family:var(--fh);font-size:clamp(24px,5vw,56px);font-weight:900;line-height:1.08;letter-spacing:-.04em;color:#fff;margin-bottom:12px">{tt}</h2><p style="color:rgba(255,255,255,.6);font-size:15px;margin-bottom:38px;max-width:440px;margin-left:auto;margin-right:auto">{sub}</p><div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap"><a style="display:inline-flex;align-items:center;gap:8px;background:#fff;color:#0A0A0A;font-weight:800;padding:17px 50px;border-radius:var(--r-btn,4px);font-size:16px;text-decoration:none" href="#">{cc} →</a><a style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.1);backdrop-filter:blur(8px);color:rgba(255,255,255,.82);font-weight:600;padding:16px 28px;border-radius:var(--r-btn,4px);border:1.5px solid rgba(255,255,255,.3);font-size:14px;text-decoration:none" href="#">카카오톡 문의</a></div></div></section>')


def sec_event_overview(d,cp,T):
    t=strip_hanja(cp.get("eventTitle",d["purpose_label"])); desc=strip_hanja(cp.get("eventDesc","이 이벤트는 기간 한정으로 진행됩니다."))
    details=cp.get("eventDetails",[["📅","이벤트 기간","2026. 4. 1 — 4. 30"],["🎯","대상","고3·N수"],["💰","혜택","최대 30% 할인"]])
    dh="".join(f'<div class="card rv d{i+1}" style="text-align:center;padding:28px 18px"><div style="font-size:34px;margin-bottom:12px">{ic}</div><div style="font-size:10px;font-weight:800;color:var(--c1);letter-spacing:.14em;text-transform:uppercase;margin-bottom:8px">{lb}</div><div style="font-family:var(--fh);font-size:18px;font-weight:700">{vl}</div></div>' for i,(ic,lb,vl) in enumerate(details))
    return f'<section class="sec" id="event-overview"><div style="max-width:1200px;margin:0 auto"><div class="rv"><div class="tag-line">이벤트 개요</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{desc}</p></div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px">{dh}</div></div></section>'

def sec_event_benefits(d,cp,T):
    t=strip_hanja(cp.get("benefitsTitle","이벤트 특별 혜택"))
    raw_b=cp.get("eventBenefits",[])
    defaults=[{"icon":"🎁","title":"수강료 특가","desc":"이벤트 기간 특별 할인 혜택을 제공합니다.","badge":"할인","no":"01"},{"icon":"📚","title":"교재 무료 제공","desc":"핵심 교재 및 학습 자료를 무료로 드립니다.","badge":"무료","no":"02"},{"icon":"🔥","title":"라이브 특강","desc":"매주 라이브 특강으로 실전 감각을 기릅니다.","badge":"매주","no":"03"}]
    benefits=raw_b if isinstance(raw_b,list) and raw_b else defaults
    def _b(b,i):
        if isinstance(b,dict): icon=b.get("icon","✦");no=b.get("no",f"{i+1:02d}");badge=strip_hanja(str(b.get("badge","혜택")));title=strip_hanja(str(b.get("title","")));desc=strip_hanja(str(b.get("desc","")))
        else: icon,no,badge,title,desc="✦",f"{i+1:02d}","혜택",strip_hanja(str(b)),""
        return f'<div class="card rv d{min(i+1,4)}" style="display:grid;grid-template-columns:56px 1fr;gap:16px;align-items:flex-start;padding:20px"><div style="width:56px;height:56px;border-radius:var(--r,4px);background:linear-gradient(135deg,var(--c1),var(--c2));display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0">{icon}</div><div><div style="display:flex;align-items:center;gap:8px;margin-bottom:7px;flex-wrap:wrap"><span style="font-size:9px;font-weight:800;color:var(--c1);opacity:.7">NO.{no}</span><span style="background:var(--c1);color:#fff;font-size:9px;font-weight:800;padding:2px 10px;border-radius:100px">{badge}</span></div><div style="font-family:var(--fh);font-size:14px;font-weight:700;margin-bottom:6px" class="st">{title}</div><p style="font-size:12.5px;line-height:1.85;color:var(--t70)">{desc}</p></div></div>'
    bh="".join(_b(b,i) for i,b in enumerate(benefits))
    return f'<section class="sec alt" id="event-benefits"><div style="max-width:1200px;margin:0 auto"><div class="rv"><div class="tag-line">이벤트 혜택</div><h2 class="sec-h2 st">{t}</h2></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px">{bh}</div></div></section>'

def sec_event_deadline(d,cp,T):
    t=strip_hanja(cp.get("deadlineTitle","마감 안내")); msg=strip_hanja(cp.get("deadlineMsg","이벤트는 기간 한정으로 운영됩니다.")); cc=strip_hanja(cp.get("ctaCopy","이벤트 신청하기"))
    timer='<div id="cdtimer" style="display:flex;gap:14px;justify-content:center;margin:26px 0 32px">'+"".join(f'<div style="text-align:center;background:rgba(255,255,255,.12);border-radius:var(--r,4px);padding:13px 18px;min-width:68px"><div id="cd_{u}" style="font-family:var(--fh);font-size:34px;font-weight:900;color:#fff;line-height:1">00</div><div style="font-size:9px;font-weight:800;color:rgba(255,255,255,.5);letter-spacing:.14em;margin-top:3px">{l}</div></div>' for u,l in [("d","DAYS"),("h","HOURS"),("m","MIN"),("s","SEC")])+'</div><script>(function(){var end=new Date(Date.now()+72*60*60*1000);function upd(){var now=new Date(),diff=Math.max(0,end-now);var dd=Math.floor(diff/864e5),hh=Math.floor((diff%864e5)/36e5),mm=Math.floor((diff%36e5)/6e4),ss=Math.floor((diff%6e4)/1e3);[["cd_d",dd],["cd_h",hh],["cd_m",mm],["cd_s",ss]].forEach(function(x){var el=document.getElementById(x[0]);if(el)el.textContent=String(x[1]).padStart(2,"0");});}upd();setInterval(upd,1000);})();</script>'
    return f'<section class="sec" id="event-deadline" style="background:{T["cta"]};text-align:center"><div class="rv" style="max-width:680px;margin:0 auto"><div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.15);padding:6px 18px;border-radius:100px;font-size:11px;font-weight:800;color:#fff;margin-bottom:18px">⏰ 마감 안내</div><h2 style="font-family:var(--fh);font-size:clamp(22px,4vw,42px);font-weight:900;color:#fff;margin-bottom:12px" class="st">{t}</h2><p style="color:rgba(255,255,255,.7);font-size:15px;line-height:1.9;max-width:460px;margin:0 auto">{msg}</p>{timer}<a style="display:inline-flex;align-items:center;gap:8px;background:#fff;color:#0A0A0A;font-weight:800;padding:16px 50px;border-radius:var(--r-btn,4px);font-size:16px;text-decoration:none" href="#">{cc} →</a></div></section>'

def sec_fest_hero(d,cp,T):
    t=strip_hanja(cp.get("festHeroTitle",f"{d['subject']} 기획전")); cc=strip_hanja(cp.get("festHeroCopy","최고의 강사들이 한 자리에")); sub=strip_hanja(cp.get("festHeroSub",f"수능 {d['subject']} 전 강사 라인업."))
    stats=cp.get("festHeroStats",[]); sh="".join(f'<div style="text-align:center"><div style="font-family:var(--fh);font-size:clamp(20px,3.5vw,34px);font-weight:900;color:var(--c1)">{sv}</div><div style="font-size:9px;color:rgba(255,255,255,.5);font-weight:700;letter-spacing:.12em;text-transform:uppercase;margin-top:4px">{sl}</div></div>' for sv,sl in stats) if stats else ""
    return f'<section id="fest-hero" style="position:relative;min-height:80vh;overflow:hidden;background:{T["cta"]};display:flex;flex-direction:column;justify-content:center;text-align:center;padding:clamp(72px,10vw,112px) clamp(22px,5vw,80px)"><div style="position:relative;z-index:2"><div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.12);backdrop-filter:blur(8px);padding:7px 20px;border-radius:var(--r-btn,4px);font-size:11px;font-weight:800;color:#fff;margin-bottom:26px;border:1px solid rgba(255,255,255,.2)">🏆 {d["subject"]} 기획전</div><h1 style="font-family:var(--fh);font-size:clamp(38px,8vw,110px);font-weight:900;line-height:.82;letter-spacing:-.05em;color:#fff;margin-bottom:20px" class="st">{t}</h1><p style="font-size:clamp(15px,2.5vw,22px);color:rgba(255,255,255,.78);margin-bottom:10px;font-weight:700">{cc}</p><p style="font-size:14px;color:rgba(255,255,255,.52);margin-bottom:48px;max-width:500px;margin-left:auto;margin-right:auto">{sub}</p>'+(f'<div style="display:flex;gap:48px;justify-content:center;flex-wrap:wrap;padding-top:36px;border-top:1px solid rgba(255,255,255,.15)">{sh}</div>' if sh else "")+"</div></section>"

def sec_fest_lineup(d,cp,T):
    t=strip_hanja(cp.get("festLineupTitle","강사 라인업")); s=strip_hanja(cp.get("festLineupSub",f"{d['subject']} 전 영역 최강 강사진"))
    lineup=cp.get("festLineup",[{"name":"강사A","tag":"독해·문법","tagline":"수능 영어 독해의 정석","badge":"베스트셀러","emoji":"📖"},{"name":"강사B","tag":"EBS 연계","tagline":"EBS 연계율 완벽 적중","badge":"적중률 1위","emoji":"🎯"},{"name":"강사C","tag":"어법·어휘","tagline":"어법·어휘 전문 빠른 풀이","badge":"속도UP","emoji":"⚡"},{"name":"강사D","tag":"파이널","tagline":"수능 D-30 파이널 완성","badge":"파이널 특화","emoji":"🏆"}])
    def _l(l,i):
        if isinstance(l,dict): emoji=l.get("emoji","📖");tag=strip_hanja(str(l.get("tag","")));name=strip_hanja(str(l.get("name","")));tagline=strip_hanja(str(l.get("tagline","")));badge=strip_hanja(str(l.get("badge","")))
        else: emoji,tag,name,tagline,badge="📖","강사","강사","강사 소개",""
        return f'<div class="card rv d{min(i+1,4)}" style="text-align:center;padding:26px 18px"><div style="font-size:38px;margin-bottom:12px">{emoji}</div><div style="display:inline-flex;align-items:center;gap:6px;background:var(--bg3);color:var(--c1);font-size:9.5px;font-weight:800;padding:4px 12px;border-radius:var(--r-btn,100px);margin-bottom:11px;border:1px solid var(--bd)">{tag}</div><div style="font-family:var(--fh);font-size:18px;font-weight:900;margin-bottom:7px" class="st">{name}</div><p style="font-size:12px;line-height:1.75;color:var(--t70);margin-bottom:11px">{tagline}</p><span style="font-size:10px;background:var(--c1);color:#fff;padding:4px 14px;border-radius:100px;font-weight:800">{badge}</span></div>'
    lh="".join(_l(l,i) for i,l in enumerate(lineup))
    return f'<section class="sec alt" id="fest-lineup"><div style="max-width:1200px;margin:0 auto"><div class="rv"><div class="tag-line">강사 라인업</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{s}</p></div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">{lh}</div></div></section>'

def sec_fest_benefits(d,cp,T):
    t=strip_hanja(cp.get("festBenefitsTitle","기획전 특별 혜택")); raw_b=cp.get("festBenefits",[])
    defaults=[{"icon":"🎁","title":"전 강사 통합 수강료 특가","desc":"최대 30% 추가 할인 혜택.","badge":"최대 30%","no":"01"},{"icon":"📚","title":"통합 학습 자료 무료","desc":"통합 교재 및 기출 자료 무료 제공.","badge":"무료 제공","no":"02"},{"icon":"🔥","title":"주간 라이브 특강","desc":"매주 전 강사 참여 라이브 특강.","badge":"전 강사","no":"03"},{"icon":"🏆","title":"목표 등급 보장","desc":"목표 등급 미달성 시 재수강 지원.","badge":"성적 보장","no":"04"}]
    benefits=raw_b if isinstance(raw_b,list) and raw_b else defaults
    def _fb(b,i):
        if isinstance(b,dict): icon=b.get("icon","✦");no=b.get("no",f"{i+1:02d}");badge=strip_hanja(str(b.get("badge","혜택")));title=strip_hanja(str(b.get("title","")));desc=strip_hanja(str(b.get("desc","")))
        else: icon,no,badge,title,desc="✦",f"{i+1:02d}","혜택",strip_hanja(str(b)),""
        return f'<div class="card rv d{min(i+1,4)}" style="display:grid;grid-template-columns:52px 1fr;gap:14px;align-items:flex-start;padding:18px"><div style="width:52px;height:52px;border-radius:var(--r,4px);background:linear-gradient(135deg,var(--c1),var(--c2));display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0">{icon}</div><div><div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap"><span style="font-size:9px;font-weight:800;color:var(--c1);opacity:.7">NO.{no}</span><span style="background:var(--c1);color:#fff;font-size:9px;font-weight:800;padding:2px 10px;border-radius:100px">{badge}</span></div><div style="font-family:var(--fh);font-size:14px;font-weight:700;margin-bottom:5px" class="st">{title}</div><p style="font-size:12px;line-height:1.85;color:var(--t70)">{desc}</p></div></div>'
    bh="".join(_fb(b,i) for i,b in enumerate(benefits))
    return f'<section class="sec" id="fest-benefits"><div style="max-width:1200px;margin:0 auto"><div class="rv"><div class="tag-line">기획전 혜택</div><h2 class="sec-h2 st">{t}</h2></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px">{bh}</div></div></section>'

def sec_fest_cta(d,cp,T):
    t=strip_hanja(cp.get("festCtaTitle",f"지금 바로 {d['subject']} 기획전<br>전체 강사 라인업을 만나세요")); s=strip_hanja(cp.get("festCtaSub",f"최고의 강사들과 함께 {d['subject']} 1등급 완성."))
    return f'<section style="padding:clamp(64px,10vw,108px) clamp(22px,5vw,72px);text-align:center;position:relative;overflow:hidden;background:{T["cta"]}"><div style="position:relative;z-index:1"><div style="display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.12);backdrop-filter:blur(8px);padding:7px 20px;border-radius:var(--r-btn,4px);font-size:11px;font-weight:800;color:#fff;margin-bottom:24px;border:1px solid rgba(255,255,255,.2)">🏆 {d["subject"]} 기획전 통합 신청</div><h2 style="font-family:var(--fh);font-size:clamp(24px,5vw,58px);font-weight:900;line-height:1.05;letter-spacing:-.04em;color:#fff;margin-bottom:16px">{t}</h2><p style="color:rgba(255,255,255,.6);font-size:15px;line-height:1.85;margin-bottom:40px;max-width:480px;margin-left:auto;margin-right:auto">{s}</p><div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap"><a style="display:inline-flex;align-items:center;gap:8px;background:#fff;color:#0A0A0A;font-weight:800;padding:18px 50px;border-radius:var(--r-btn,4px);font-size:16px;text-decoration:none" href="#">기획전 통합 신청 →</a></div></div></section>'

def sec_video(d,cp,T):
    yt_url=cp.get("videoUrl",""); yt_title=strip_hanja(cp.get("videoTitle",f"{d['name']} 선생님이 말하는 {d['purpose_label']}의 본질")); yt_sub=strip_hanja(cp.get("videoSub",f"수강 전 꼭 확인하세요 — {d['subject']} 공부의 본질이 바뀝니다.")); tag_txt=cp.get("videoTag","OFFICIAL TRAILER")
    embed=f'<div style="position:relative;width:100%;padding-bottom:56.25%;border-radius:var(--r,4px);overflow:hidden;border:1px solid var(--bd)"><iframe src="{yt_url}" style="position:absolute;inset:0;width:100%;height:100%;border:none" allowfullscreen allow="autoplay;encrypted-media"></iframe></div>' if yt_url and "youtube" in yt_url else f'<div style="position:relative;width:100%;padding-bottom:56.25%;background:var(--bg3);border-radius:var(--r,4px);overflow:hidden;border:1px solid var(--bd)"><div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px"><div style="width:68px;height:68px;border-radius:50%;background:var(--c1);display:flex;align-items:center;justify-content:center"><div style="width:0;height:0;border-style:solid;border-width:13px 0 13px 26px;border-color:transparent transparent transparent #fff;margin-left:5px"></div></div><div style="font-size:13px;color:var(--t45);font-weight:600">영상 재생하기</div></div></div>'
    return f'<section class="sec alt" id="video"><div style="max-width:1100px;margin:0 auto"><div class="rv" style="text-align:center;margin-bottom:32px"><div style="display:inline-flex;align-items:center;gap:8px;background:var(--c1);color:#fff;font-size:9.5px;font-weight:800;padding:5px 16px;border-radius:var(--r-btn,4px);margin-bottom:14px;letter-spacing:.12em">▶ {tag_txt}</div><h2 class="sec-h2 st" style="text-align:center">{yt_title}</h2><p class="sec-sub" style="text-align:center">{yt_sub}</p></div><div class="rv d1">{embed}</div></div></section>'

def sec_before_after(d,cp,T):
    t=strip_hanja(cp.get("baTitle","공부 방식이 이렇게 달라집니다")); sub=strip_hanja(cp.get("baSub",f"{d['purpose_label']} 이후의 변화"))
    befores=cp.get("baBeforeItems",[f"{d['subject']} 지문이 무슨 말인지 몰라 처음부터 다 읽는다","시간이 부족해 뒷문제를 찍는 일이 반복된다","아는 내용인데 시험장에서 실수가 계속 나온다"])
    afters=cp.get("baAfterItems",["구조가 보여서 필요한 부분만 정확히 읽는다","시간이 10분 이상 남아 검토까지 완료한다","실전에서 배운 대로 정확히 풀어낸다"])
    bh="".join(f'<div style="display:flex;gap:10px;align-items:flex-start;padding:11px 0;border-bottom:1px solid rgba(255,80,80,.1)"><div style="flex-shrink:0;width:20px;height:20px;border-radius:50%;background:rgba(255,80,80,.2);border:1.5px solid #FF5050;display:flex;align-items:center;justify-content:center;font-size:10px;color:#FF5050;font-weight:900;margin-top:1px">✕</div><p style="font-size:13px;line-height:1.75;color:rgba(255,255,255,.65);margin:0">{strip_hanja(b)}</p></div>' for b in befores)
    ah="".join(f'<div style="display:flex;gap:10px;align-items:flex-start;padding:11px 0;border-bottom:1px solid var(--bd)"><div style="flex-shrink:0;width:20px;height:20px;border-radius:50%;background:var(--c1);display:flex;align-items:center;justify-content:center;font-size:10px;color:#fff;font-weight:900;margin-top:1px">✓</div><p style="font-size:13px;line-height:1.75;color:var(--text);margin:0;font-weight:500">{strip_hanja(a)}</p></div>' for a in afters)
    return (f'<section class="sec" id="before-after"><div style="max-width:1100px;margin:0 auto"><div class="rv" style="text-align:center;margin-bottom:40px"><div class="tag-line" style="justify-content:center">수강 전/후</div><h2 class="sec-h2 st" style="text-align:center">{t}</h2><p class="sec-sub" style="text-align:center">{sub}</p></div>'
             f'<div style="display:grid;grid-template-columns:1fr 60px 1fr;gap:0;align-items:stretch" class="rv d1">'
             f'<div style="background:#1A0808;border-radius:var(--r,4px) 0 0 var(--r,4px);padding:26px;border:1px solid rgba(255,80,80,.25);border-right:none"><div style="font-size:11px;font-weight:800;color:#FF5050;letter-spacing:.14em;text-transform:uppercase;margin-bottom:16px;display:flex;align-items:center;gap:8px"><div style="width:8px;height:8px;border-radius:50%;background:#FF5050"></div>BEFORE</div>{bh}</div>'
             f'<div style="background:var(--c1);display:flex;align-items:center;justify-content:center"><div style="font-family:var(--fh);font-size:20px;font-weight:900;color:#fff">→</div></div>'
             f'<div style="background:var(--bg3);border-radius:0 var(--r,4px) var(--r,4px) 0;padding:26px;border:1px solid var(--bd);border-left:none"><div style="font-size:11px;font-weight:800;color:var(--c1);letter-spacing:.14em;text-transform:uppercase;margin-bottom:16px;display:flex;align-items:center;gap:8px"><div style="width:8px;height:8px;border-radius:50%;background:var(--c1)"></div>AFTER</div>{ah}</div>'
             f'</div></div></section>')

def sec_method(d,cp,T):
    t=strip_hanja(cp.get("methodTitle",f"{d['name'] or d['subject']} 시그니처 학습법")); sub=strip_hanja(cp.get("methodSub","이 방식으로 접근하면 지문이 완전히 달리 보입니다"))
    methods_raw=cp.get("methodSteps",[]); ip=st.session_state.get("inst_profile") or {}
    sig=[strip_hanja(m) for m in (ip.get("signatureMethods") or []) if m and m not in ("없음","")]
    if not methods_raw:
        methods_raw=[{"step":f"STEP {i+1:02d}","label":s,"desc":f"{s} 방식으로 {d['subject']} 지문에 접근합니다."} for i,s in enumerate(sig[:3])] if sig else [{"step":"STEP 01","label":"파악","desc":f"{d['subject']} 구조를 파악합니다."},{"step":"STEP 02","label":"분석","desc":"핵심 논리를 분석합니다."},{"step":"STEP 03","label":"적용","desc":"실전 문제에 즉시 적용합니다."}]
    sh="".join(f'<div class="rv d{min(i+1,4)}" style="display:flex;gap:0;align-items:stretch;margin-bottom:10px"><div style="min-width:84px;background:var(--c1);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:16px 10px;border-radius:var(--r,4px) 0 0 var(--r,4px)"><div style="font-family:var(--fh);font-size:10px;font-weight:900;color:rgba(255,255,255,.6);letter-spacing:.1em">{strip_hanja(str(m.get("step",f"STEP {i+1:02d}")))}</div><div style="font-family:var(--fh);font-size:16px;font-weight:900;color:#fff;margin-top:2px">{strip_hanja(str(m.get("label",f"{i+1}단계")))}</div></div><div style="flex:1;background:var(--bg3);padding:16px 22px;border-radius:0 var(--r,4px) var(--r,4px) 0;border:1px solid var(--bd);border-left:none;display:flex;align-items:center"><p style="font-size:14px;line-height:1.8;color:var(--text);margin:0;font-weight:500">{strip_hanja(str(m.get("desc","")))}</p></div></div>' for i,m in enumerate(methods_raw))
    return (f'<section class="sec alt" id="method"><div style="display:grid;grid-template-columns:1fr 1.4fr;gap:72px;align-items:center;max-width:1200px;margin:0 auto"><div class="rv" style="position:sticky;top:60px"><div class="tag-line">학습법</div><h2 class="sec-h2 st">{t}</h2><p class="sec-sub">{sub}</p>'
             f'<div style="margin-top:22px;padding:18px 22px;border:1.5px solid var(--c1);border-radius:var(--r,4px)"><div style="font-size:10px;font-weight:800;letter-spacing:.14em;color:var(--c1);text-transform:uppercase;margin-bottom:7px">핵심 공식</div><div style="font-family:var(--fh);font-size:clamp(16px,2vw,22px);font-weight:900;color:var(--text)">'+(" → ".join(sig[:3]) if sig else f"{d['subject']} 완성 공식")+f'</div></div></div><div class="rv d1">{sh}</div></div></section>')

def sec_package(d,cp,T):
    t=strip_hanja(cp.get("pkgTitle",f"{d['purpose_label']} 구성 안내")); sub=strip_hanja(cp.get("pkgSub","지금 신청하면 아래 구성이 모두 포함됩니다"))
    pkgs=cp.get("packages",[{"icon":"📗","name":"강의 수강권","desc":f"{d['purpose_label']} 전체 강의 무제한 수강","badge":"필수"},{"icon":"📖","name":"PDF 교재","desc":"핵심 이론·기출 정리 PDF 파일 제공","badge":"포함"},{"icon":"🎯","name":"실전 모의고사","desc":"단계별 실전 모의고사 3회분 제공","badge":"포함"},{"icon":"💬","name":"질문 게시판","desc":"강사 직접 답변 질문 게시판 무제한 이용","badge":"특전"}])
    ph="".join(f'<div class="rv d{min(i+1,4)}" style="display:flex;gap:14px;align-items:center;padding:16px 20px;border:1px solid var(--bd);border-radius:var(--r,4px);background:var(--bg);margin-bottom:8px"><div style="font-size:28px;flex-shrink:0">{p.get("icon","📦") if isinstance(p,dict) else "📦"}</div><div style="flex:1"><div style="font-family:var(--fh);font-size:14px;font-weight:700;color:var(--text);margin-bottom:2px" class="st">{strip_hanja(str(p.get("name","") if isinstance(p,dict) else p))}</div><p style="font-size:12.5px;line-height:1.7;color:var(--t70);margin:0">{strip_hanja(str(p.get("desc","") if isinstance(p,dict) else ""))}</p></div>'+(lambda _b: f'<span style="flex-shrink:0;font-size:10px;font-weight:800;background:{"var(--c1)" if _b=="필수" else "var(--bg3)"};color:{"#fff" if _b=="필수" else "var(--c1)"};padding:5px 12px;border-radius:var(--r-btn,100px);border:1.5px solid var(--c1)">{_b}</span>')(strip_hanja(str(p.get("badge","포함") if isinstance(p,dict) else "포함")))+'</div>' for i,p in enumerate(pkgs))
    return f'<section class="sec" id="package"><div style="max-width:900px;margin:0 auto"><div class="rv" style="text-align:center;margin-bottom:32px"><div class="tag-line" style="justify-content:center">구성 안내</div><h2 class="sec-h2 st" style="text-align:center">{t}</h2><p class="sec-sub" style="text-align:center">{sub}</p></div><div class="rv d1">{ph}</div></div></section>'

def sec_custom(d,cp,T):
    c=cp.get("custom_section_data",{})
    if not c: return ""
    tag=strip_hanja(c.get("tag","추가 안내")); title=strip_hanja(c.get("title","추가 섹션")); items=c.get("items",[]); desc=strip_hanja(c.get("desc",""))
    if items:
        ih="".join(f'<div class="card rv d{min(i+1,3)}"><div style="display:flex;align-items:center;gap:12px;margin-bottom:10px"><div style="width:38px;height:38px;min-width:38px;border-radius:var(--r,4px);background:var(--c1);display:flex;align-items:center;justify-content:center;font-size:17px">{it.get("icon","✦")}</div><div style="font-family:var(--fh);font-size:14px;font-weight:700" class="st">{strip_hanja(it.get("title",""))}</div></div><p style="font-size:12.5px;line-height:1.9;color:var(--t70)">{strip_hanja(it.get("desc",""))}</p></div>' for i,it in enumerate(items))
        body=f'<div style="display:grid;grid-template-columns:repeat({min(len(items),3)},1fr);gap:12px" class="rv d1">{ih}</div>'
    else:
        body=f'<div class="rv d1"><p style="font-size:14px;line-height:1.9;color:var(--t70)">{desc}</p></div>'
    return f'<section class="sec" id="custom-section"><div style="max-width:1200px;margin:0 auto"><div class="rv"><div class="tag-line">{tag}</div><h2 class="sec-h2 st">{title}</h2></div>{body}</div></section>'


# ══════════════════════════════════════════════════════
# HTML 빌더
# ══════════════════════════════════════════════════════
def build_html(secs:list)->str:
    T=get_theme(); cp=dict(st.session_state.custom_copy or {})
    if st.session_state.get("uploaded_bg_b64"): cp["bg_photo_url"]=st.session_state.uploaded_bg_b64
    elif st.session_state.bg_photo_url: cp["bg_photo_url"]=st.session_state.bg_photo_url
    d={"name":st.session_state.instructor_name or "","subject":st.session_state.subject,"purpose_label":st.session_state.purpose_label,"target":st.session_state.target}
    if st.session_state.concept=="custom" and st.session_state.custom_theme:
        T["heroStyle"]=st.session_state.custom_theme.get("heroStyle","typographic")
    else:
        T["heroStyle"]=THEMES.get(st.session_state.concept,{}).get("heroStyle","typographic")
    dc=".card{background:var(--bg2)!important}" if T["dark"] else ""
    mp={"banner":sec_banner,"intro":sec_intro,"why":sec_why,"curriculum":sec_curriculum,
        "target":sec_target,"reviews":sec_reviews,"faq":sec_faq,"cta":sec_cta,
        "video":sec_video,"before_after":sec_before_after,"method":sec_method,"package":sec_package,
        "event_overview":sec_event_overview,"event_benefits":sec_event_benefits,"event_deadline":sec_event_deadline,
        "fest_hero":sec_fest_hero,"fest_lineup":sec_fest_lineup,"fest_benefits":sec_fest_benefits,
        "fest_cta":sec_fest_cta,"custom_section":sec_custom}
    body="\n".join(mp[s](d,cp,T) for s in secs if s in mp)
    ttl=cp.get("bannerTitle",cp.get("festHeroTitle",d["purpose_label"]))
    particle_js=_particle_js(T.get("particle","none"))
    # 테마 코딩 효과
    concept=st.session_state.concept
    theme_fx=_theme_effects_html(concept)
    # 모바일 플로팅 CTA
    cta_txt=strip_hanja(cp.get("ctaCopy","수강신청하기"))
    mob_cta=(f'<nav class="mob-cta"><a href="#">{cta_txt} →</a><a href="#">문의하기</a></nav>')
    # 스크롤 애니메이션 JS
    scroll_js='<script>const ro=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){e.target.classList.add("on");ro.unobserve(e.target);}})},{threshold:.08});document.querySelectorAll(".rv").forEach(el=>ro.observe(el));</script>'
    return (f'<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"/>'
            f'<meta name="viewport" content="width=device-width,initial-scale=1.0,viewport-fit=cover"/>'
            f'<meta name="theme-color" content="#000000"/>'
            f'<title>{d["name"]} {d["subject"]} · {ttl}</title>'
            f'<link rel="preconnect" href="https://fonts.googleapis.com"/>'
            f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>'
            f'<link href="{T["fonts"]}" rel="stylesheet"/>'
            f'<style>:root{{{T["vars"]}}}{BASE_CSS}{T["extra_css"]}{dc}</style>'
            f'</head><body>{theme_fx}{body}{mob_cta}{particle_js}{scroll_js}'
            f'</body></html>')


# ══════════════════════════════════════════════════════
# UI CSS (사이드바 + 메인)
# ══════════════════════════════════════════════════════
st.markdown("""<style>
[data-testid="stSidebar"]{background:#07080F;border-right:1px solid #161A28;}
[data-testid="stSidebar"] label,[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span:not(.stCheckbox span){color:#8A9AB8!important;font-size:12px!important;}
[data-testid="stSidebar"] h3{color:#E0E8F8!important;font-size:16px!important;font-weight:800!important;}
[data-testid="stSidebar"] hr{border-color:#171D2F!important;}
.stButton>button{border-radius:6px!important;font-weight:700!important;border:1px solid #232A40!important;background:#0D1220!important;color:#8A9AB8!important;transition:all .15s!important;font-size:12px!important;}
.stButton>button:hover{background:#161E38!important;color:#C0CDE8!important;border-color:#343C58!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#FF6B35,#E84393)!important;color:#fff!important;border:none!important;font-size:13px!important;}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{background:linear-gradient(135deg,#FF4500,#FF1493,#7B2FFF)!important;color:#fff!important;font-weight:800!important;box-shadow:0 0 22px rgba(255,69,0,.5)!important;animation:pulse-btn 2.5s ease-in-out infinite!important;}
@keyframes pulse-btn{0%,100%{box-shadow:0 0 22px rgba(255,69,0,.5)}50%{box-shadow:0 0 32px rgba(255,20,147,.75)}}
div[data-testid="stMetric"]{background:#090D1C;border:1px solid #1A2038;border-radius:10px;padding:14px;}
div[data-testid="stMetric"] label{color:#4A5870!important;font-size:11px!important;}
div[data-testid="stMetric"] div{color:#E0E8F8!important;font-weight:700!important;}
[data-testid="stSidebar"] input,[data-testid="stSidebar"] textarea,[data-testid="stSidebar"] select{background:#090D1C!important;border:1px solid #1A2038!important;color:#C0CDE8!important;border-radius:6px!important;font-size:12px!important;}
.stMainBlockContainer{background:#0A0C14;color:#E0E8F8;}
.stMainBlockContainer p,.stMainBlockContainer span,.stMainBlockContainer label,.stMainBlockContainer div{color:#B8C8E0;}
.stMainBlockContainer h1,.stMainBlockContainer h2,.stMainBlockContainer h3,.stMainBlockContainer h4{color:#E0E8F8!important;}
.stMarkdown{color:#B8C8E0!important;}
.stSuccess{background:rgba(52,211,153,.08)!important;border:1px solid rgba(52,211,153,.2)!important;}
.stInfo{background:rgba(99,102,241,.08)!important;border:1px solid rgba(99,102,241,.2)!important;}
.stError{background:rgba(248,113,113,.08)!important;border:1px solid rgba(248,113,113,.2)!important;}
.sec-hdr{font-size:9.5px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#3A4868;padding:10px 16px 5px;}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🎓 강사 페이지 빌더 Pro")
    st.caption("수능 강사 랜딩페이지 AI 생성기 v7.5")
    st.divider()

    st.markdown('<div class="sec-hdr">🔑 GROQ API KEY</div>',unsafe_allow_html=True)
    api_in=st.text_input("API Key",type="password",value=st.session_state.api_key,placeholder="gsk_...",label_visibility="collapsed")
    if api_in!=st.session_state.api_key: st.session_state.api_key=api_in
    if st.session_state.api_key: st.success("✓ Groq API 키 입력됨 (완전 무료)",icon="✅")
    else: st.markdown('<a href="https://console.groq.com" target="_blank" style="font-size:11px;color:#5A6A8A">👆 console.groq.com → API Keys → Create</a>',unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="sec-hdr">📋 페이지 목적</div>',unsafe_allow_html=True)
    pt=st.radio("목적",list(PURPOSE_SECTIONS.keys()),index=list(PURPOSE_SECTIONS.keys()).index(st.session_state.purpose_type),label_visibility="collapsed")
    if pt!=st.session_state.purpose_type:
        st.session_state.purpose_type=pt
        st.session_state.active_sections=PURPOSE_SECTIONS[pt].copy()
        st.session_state.custom_copy=None
        # ★ Fix 5: 목적 변경 시 추천 테마 자동 적용
        recommended=PURPOSE_DEFAULT_THEME.get(pt,"acid")
        if st.session_state.concept not in ["custom"] and st.session_state.concept!=recommended:
            st.session_state.concept=recommended
            st.session_state.custom_theme=None
        st.rerun()
    st.caption(PURPOSE_HINTS[pt])
    st.divider()

    st.markdown('<div class="sec-hdr">🎨 페이지 컨셉</div>',unsafe_allow_html=True)
    if st.button("🎲 AI 랜덤 — 매번 완전히 새 디자인!",type="primary",use_container_width=True):
        if not st.session_state.api_key: st.warning("API 키를 먼저 입력해주세요")
        else:
            seed=random.choice(RANDOM_SEEDS)
            while len(RANDOM_SEEDS)>1 and seed==st.session_state.last_seed: seed=random.choice(RANDOM_SEEDS)
            st.session_state.last_seed=seed
            with st.spinner(f"'{seed['mood'][:22]}...' 생성 중..."):
                try:
                    r=gen_concept(seed); st.session_state.custom_theme=r; st.session_state.concept="custom"
                    bg=build_bg_url(seed["mood"]); st.session_state.bg_photo_url=bg
                    st.success(f"✓ '{r.get('name','새 컨셉')}' 생성!"); st.rerun()
                except Exception as e: st.error(f"실패: {e}")

    mood_in=st.text_area("직접 무드 묘사:",height=75,value=st.session_state.ai_mood,placeholder="예: 사람 많은 광장 밤\n예: 에펠탑 파리 야경\n예: 관중이 가득찬 야구장",label_visibility="visible")
    st.session_state.ai_mood=mood_in
    if st.button("✦ 이 무드로 AI 컨셉 생성",use_container_width=True):
        if not mood_in.strip(): st.warning("무드를 입력해주세요")
        elif not st.session_state.api_key: st.warning("API 키를 먼저 입력해주세요")
        else:
            with st.spinner("AI 컨셉 생성 중..."):
                try:
                    r=gen_concept({"mood":mood_in.strip(),"layout":"auto","font":"auto","particle":"none"})
                    st.session_state.custom_theme=r; st.session_state.concept="custom"
                    bg=build_bg_url(mood_in.strip()); st.session_state.bg_photo_url=bg; st.session_state.uploaded_bg_b64=""
                    st.success(f"✓ '{r.get('name','새 컨셉')}' 생성됨!"); st.rerun()
                except Exception as e: st.error(f"실패: {e}")

    st.markdown("**🖼 배경 이미지 업로드**")
    st.caption("원하는 이미지를 직접 올리면 히어로 배경으로 사용됩니다")
    uploaded_img=st.file_uploader("배경 이미지",type=["jpg","jpeg","png","webp"],label_visibility="collapsed",key="bg_uploader")
    if uploaded_img is not None:
        b64=base64.b64encode(uploaded_img.read()).decode(); mime=uploaded_img.type or "image/jpeg"
        st.session_state.uploaded_bg_b64=f"data:{mime};base64,{b64}"; st.session_state.bg_photo_url=""
        st.success(f"✓ '{uploaded_img.name}' 업로드됨!"); st.rerun()
    if st.session_state.uploaded_bg_b64:
        if st.button("🗑 업로드 이미지 제거",use_container_width=True,key="rm_bg"):
            st.session_state.uploaded_bg_b64=""; st.rerun()

    if "video" in st.session_state.active_sections:
        st.markdown("**🎬 YouTube embed URL**")
        cur_yt=(st.session_state.custom_copy or {}).get("videoUrl","") if st.session_state.custom_copy else ""
        yt_in=st.text_input("YouTube URL",value=cur_yt,placeholder="https://www.youtube.com/embed/...",label_visibility="collapsed",key="yt_url_input")
        if yt_in and yt_in!=cur_yt:
            if st.session_state.custom_copy is None: st.session_state.custom_copy={}
            st.session_state.custom_copy["videoUrl"]=yt_in; st.rerun()

    st.caption("▼ 프리셋 테마:")
    new_themes=["stadium","acid","cinematic","floral","inception","violet_pop","brutal","amber"]
    old_themes=["sakura","fire","ocean","luxury","cosmos","winter","eco"]
    st.caption("✨ 신규")
    cols_n=st.columns(2)
    for i,k in enumerate(new_themes):
        with cols_n[i%2]:
            if st.button(THEMES[k]["label"],key=f"th_{k}",type="primary" if st.session_state.concept==k else "secondary",use_container_width=True):
                st.session_state.concept=k; st.session_state.custom_theme=None; st.session_state.bg_photo_url=""; st.rerun()
    st.caption("기존")
    cols_o=st.columns(2)
    for i,k in enumerate(old_themes):
        with cols_o[i%2]:
            if st.button(THEMES[k]["label"],key=f"th_{k}",type="primary" if st.session_state.concept==k else "secondary",use_container_width=True):
                st.session_state.concept=k; st.session_state.custom_theme=None; st.session_state.bg_photo_url=""; st.rerun()

    if st.session_state.concept=="custom" and st.session_state.custom_theme:
        ct=st.session_state.custom_theme
        st.success(f"✦ AI 커스텀: {ct.get('name','?')} | {ct.get('heroStyle','?')}",icon="🎨")

    st.divider()
    st.markdown('<div class="sec-hdr">👤 강사 정보</div>',unsafe_allow_html=True)
    na_,su_=st.columns([3,2])
    with na_: nm=st.text_input("강사명",value=st.session_state.instructor_name,placeholder="강사명",label_visibility="collapsed"); st.session_state.instructor_name=nm
    with su_: sb=st.selectbox("과목",["영어","수학","국어","사회","과학"],index=["영어","수학","국어","사회","과학"].index(st.session_state.subject),label_visibility="collapsed"); st.session_state.subject=sb
    if st.button("🔍 강사 정보 자동 검색",use_container_width=True):
        if not nm: st.warning("강사명을 입력해주세요")
        elif not st.session_state.api_key: st.warning("API 키를 입력해주세요")
        else:
            with st.spinner(f"{nm} 선생님 정보 검색 중..."):
                try:
                    p=search_instructor(nm,sb); st.session_state.inst_profile=p
                    if p.get("found"):
                        st.success(f"✓ {nm} 선생님 정보 검색 완료!")
                        if p.get("slogan"): st.caption(f'💬 "{p["slogan"]}"')
                        methods=[m for m in (p.get("signatureMethods") or []) if m and m!="없음"]
                        if methods: st.caption(f'📚 {", ".join(methods)}')
                    else: st.info("정보를 찾지 못했습니다.")
                except Exception as e: st.error(f"검색 실패: {e}")

    st.divider()
    st.markdown('<div class="sec-hdr">📝 강의 브랜드명</div>',unsafe_allow_html=True)
    pl=st.text_input("브랜드명",value=st.session_state.purpose_label,placeholder="2026 수능 파이널 완성",label_visibility="collapsed"); st.session_state.purpose_label=pl
    st.markdown('<div class="sec-hdr">🎯 수강 대상</div>',unsafe_allow_html=True)
    tgt=st.radio("대상",["고3·N수","고1·2 — 기초 완성"],horizontal=True,label_visibility="collapsed"); st.session_state.target=tgt
    st.divider()

    st.markdown('<div class="sec-hdr">📑 섹션 ON/OFF</div>',unsafe_allow_html=True)
    for sid in PURPOSE_SECTIONS[st.session_state.purpose_type]:
        chk=st.checkbox(SEC_LABELS.get(sid,sid),value=sid in st.session_state.active_sections,key=f"sec_{sid}")
        if chk and sid not in st.session_state.active_sections: st.session_state.active_sections.append(sid)
        elif not chk and sid in st.session_state.active_sections: st.session_state.active_sections.remove(sid)
    st.markdown("---")
    csec_on=st.checkbox("✏️ 기타 섹션 추가",value=st.session_state.custom_section_on,key="chk_cs"); st.session_state.custom_section_on=csec_on
    if csec_on:
        if "custom_section" not in st.session_state.active_sections: st.session_state.active_sections.append("custom_section")
        ct_in=st.text_input("섹션 주제",value=st.session_state.custom_section_topic,placeholder="예: 수강평 이벤트, 공지사항",label_visibility="collapsed",key="cs_topic"); st.session_state.custom_section_topic=ct_in
        if st.button("✦ AI로 섹션 생성",use_container_width=True,key="gen_cs"):
            if not ct_in.strip(): st.warning("주제를 입력해주세요")
            elif not st.session_state.api_key: st.warning("API 키 필요")
            else:
                with st.spinner(f"'{ct_in}' 섹션 생성 중..."):
                    try:
                        r=gen_custom_sec(ct_in)
                        if st.session_state.custom_copy is None: st.session_state.custom_copy={}
                        st.session_state.custom_copy["custom_section_data"]=r; st.success(f"✓ '{r.get('title','섹션')}' 생성됨!"); st.rerun()
                    except Exception as e: st.error(f"실패: {e}")
    else:
        if "custom_section" in st.session_state.active_sections: st.session_state.active_sections.remove("custom_section")


# ══════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════
ordered=[s for s in PURPOSE_SECTIONS[st.session_state.purpose_type] if s in st.session_state.active_sections]
if st.session_state.custom_section_on and "custom_section" not in ordered:
    if st.session_state.custom_copy and st.session_state.custom_copy.get("custom_section_data"):
        ordered.append("custom_section")

final_html=build_html(ordered)
T_now=get_theme()

L,R=st.columns([1,2],gap="large")

with L:
    st.markdown("### ✍️ AI 문구 생성")
    st.caption(PURPOSE_HINTS[st.session_state.purpose_type])
    ph_map={"신규 커리큘럼":"예: 2026 수능 영어 파이널. 션티 선생님의 KISS Logic 방법론.","이벤트":"예: 파노라마 완강 기념 수강후기 이벤트. 기간 한정.","기획전":"예: 2026 영어 기획전. 독해·EBS·어법·파이널 4인 강사 통합."}
    ctx=st.text_area("페이지 맥락",height=100,placeholder=ph_map.get(st.session_state.purpose_type,"맥락 입력"),help="강사 정보 검색 후 생성하면 더 정확한 문구가 나옵니다.")
    if st.button(f"✦ {st.session_state.purpose_type} 문구 AI 생성",type="primary",use_container_width=True):
        if not ctx.strip(): st.warning("페이지 맥락을 입력해주세요")
        elif not st.session_state.api_key: st.warning("API 키를 먼저 입력해주세요")
        else:
            with st.spinner("문구 생성 중... (10~20초)"):
                try:
                    r=gen_copy(ctx,st.session_state.purpose_type,st.session_state.target,st.session_state.purpose_label)
                    st.session_state.custom_copy=r; st.success("✓ 문구 생성 완료!")
                except Exception as e: st.error(f"생성 실패: {e}")
    if st.session_state.custom_copy:
        st.success("✓ AI 문구 적용됨",icon="✅")
        if st.button("✕ 문구 초기화",use_container_width=True):
            st.session_state.custom_copy=None; st.rerun()

    st.divider()
    st.markdown("### 🎲 섹션별 문구 재생성")
    st.caption("클릭 시 해당 섹션 문구만 새롭게 교체됩니다")
    regen_secs=[s for s in ordered if s in SEC_LABELS and s!="custom_section"]
    SEC_SHORT={"banner":"배너","intro":"소개","why":"이유","curriculum":"커리큘럼","target":"대상","reviews":"수강평","faq":"FAQ","cta":"CTA","video":"영상","before_after":"전/후","method":"학습법","package":"구성","event_overview":"개요","event_benefits":"혜택","event_deadline":"마감","fest_hero":"히어로","fest_lineup":"라인업","fest_benefits":"혜택","fest_cta":"CTA"}
    if regen_secs and st.session_state.api_key:
        for row_start in range(0,len(regen_secs),4):
            chunk=regen_secs[row_start:row_start+4]; cols_r=st.columns(len(chunk))
            for i,sid in enumerate(chunk):
                label=SEC_SHORT.get(sid,sid)
                with cols_r[i]:
                    if st.button(f"↺ {label}",key=f"regen_{sid}",use_container_width=True):
                        with st.spinner(f"{label} 재생성..."):
                            try:
                                r=gen_section(sid)
                                if st.session_state.custom_copy is None: st.session_state.custom_copy={}
                                st.session_state.custom_copy.update(r); st.rerun()
                            except Exception as e: st.error(f"실패: {e}")
    elif not st.session_state.api_key: st.caption("API 키를 입력하면 활성화됩니다.")

    st.divider()
    st.markdown("### ✏️ 문구 직접 편집")
    if st.session_state.custom_copy:
        cp=st.session_state.custom_copy
        edit_secs=[]
        pt=st.session_state.purpose_type
        if pt=="신규 커리큘럼":
            edit_secs=[("🏠 배너",[("text_input","메인 제목","bannerTitle"),("text_area","리드 문구","bannerLead"),("text_input","버튼 텍스트","ctaCopy"),("text_input","브랜드 문구","brandTagline")]),("👤 강사 소개",[("text_input","소개 제목","introTitle"),("text_area","소개 본문","introDesc"),("text_input","한줄 약력","introBio")]),("📣 CTA",[("text_area","CTA 제목","ctaTitle"),("text_input","서브문구","ctaSub"),("text_input","버튼 텍스트","ctaCopy")])]
        elif pt=="이벤트":
            edit_secs=[("🏠 배너",[("text_input","메인 제목","bannerTitle"),("text_area","리드 문구","bannerLead")]),("⏰ 마감 안내",[("text_input","마감 제목","deadlineTitle"),("text_area","마감 메시지","deadlineMsg")])]
        elif pt=="기획전":
            edit_secs=[("🏆 히어로",[("text_input","히어로 제목","festHeroTitle"),("text_input","서브 카피","festHeroCopy"),("text_area","설명","festHeroSub")])]
        for sec_label,fields in edit_secs:
            with st.expander(sec_label,expanded=False):
                changed={}
                for ftype,flabel,fkey in fields:
                    cur_val=cp.get(fkey,""); wkey=f"ed_{fkey}"
                    val=st.text_area(flabel,value=cur_val,height=72,key=wkey) if ftype=="text_area" else st.text_input(flabel,value=cur_val,key=wkey)
                    if val!=cur_val: changed[fkey]=val
                if changed:
                    if st.button("✓ 적용",key=f"apply_{sec_label}"):
                        st.session_state.custom_copy.update(changed); st.rerun()
    else:
        st.caption("💡 AI로 문구를 먼저 생성하면 여기서 항목별로 수정할 수 있습니다.")

    st.divider()
    st.markdown("### 📥 HTML 내보내기")
    cn=(st.session_state.custom_theme.get("name","custom") if st.session_state.concept=="custom" and st.session_state.custom_theme else st.session_state.concept)
    st.download_button("📥 HTML 파일 다운로드",data=final_html.encode("utf-8"),file_name=f"{st.session_state.instructor_name or 'page'}_{st.session_state.subject}_{cn}.html",mime="text/html",use_container_width=True)

with R:
    col_prev,col_ref=st.columns([4,1])
    with col_prev: st.markdown("### 👁 실시간 미리보기")
    with col_ref:
        # ★ Fix 4: 새로고침 버튼 — counter 증가로 실제 rerun 트리거
        if st.button("🔄",key=f"refresh_{st.session_state.preview_ver}",help="미리보기 새로고침"):
            st.session_state.preview_ver+=1
            st.rerun()

    td=(st.session_state.custom_theme.get("name","AI 커스텀") if st.session_state.concept=="custom" and st.session_state.custom_theme else THEMES.get(st.session_state.concept,{}).get("label",""))
    m1,m2,m3=st.columns(3)
    with m1: st.metric("컨셉",td)
    with m2: st.metric("히어로",T_now.get("heroStyle","—"))
    with m3: st.metric("섹션 수",len(ordered))

    import streamlit.components.v1 as components
    # ★ Fix 4: preview_ver를 key에 포함해 매번 새 컴포넌트 렌더링
    components.html(final_html,height=900,scrolling=True,key=f"preview_html_{st.session_state.preview_ver}")
