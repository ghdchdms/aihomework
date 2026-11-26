import json
import uuid
from datetime import date
from pathlib import Path

import requests
import streamlit as st

# ------------------------------------------------------------
# 잠뜰 TV 팬 웹 - Streamlit edition
# 기존 HTML의 파란 하늘색 테마, 시리즈/단편/후기 구조를 유지합니다.
# Firebase 설정은 .streamlit/secrets.toml 에서 읽습니다.
# ------------------------------------------------------------

st.set_page_config(
    page_title="잠뜰 TV 팬 웹",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

MEMBERS = [
    {"id": "rather", "name": "라더", "color": "#ff6b6b"},
    {"id": "duckgae", "name": "덕개", "color": "#ffa94d"},
    {"id": "heptagram", "name": "각별", "color": "#f5d000"},
    {"id": "dino", "name": "공룡", "color": "#51cf66"},
    {"id": "sleepground", "name": "잠뜰", "color": "#74c0fc"},
    {"id": "suhyun", "name": "수현", "color": "#b197fc"},
]
EMOJIS = ["🎬", "🔍", "👁", "🧟", "🌀", "🏃", "✨", "⚔️", "🕵️", "🌙",
          "🔮", "🏚️", "🧩", "💀", "🌊", "🎭", "🌸", "🐣", "🍀", "🎪"]
COLORS = [m["color"] for m in MEMBERS]
DEFAULT_COLOR = COLORS[4]

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Gaegu:wght@400;700&display=swap');
:root { --sky:#56b4f5; --deep:#2196e0; --pale:#e8f6ff; --mist:#f0f9ff; }
html, body, [class*="css"] { font-family:'Noto Sans KR',sans-serif; }
.stApp { background: #f0f8ff; color:#2d3a4a; }
.block-container { max-width: 900px; padding-top: 1.1rem; padding-bottom: 3rem; }
.hero {
  background:linear-gradient(135deg,#56b4f5,#2196e0); color:white;
  border-radius:22px; padding:18px 22px; margin-bottom:16px;
  box-shadow:0 5px 20px rgba(33,150,224,.22);
}
.hero h1 { font-family:'Gaegu',cursive; font-size:2rem; margin:0; color:white; }
.hero p { margin:.25rem 0 0; opacity:.92; font-size:.9rem; }
div[data-testid="stTabs"] button { font-weight:700; }
div[data-testid="stMetric"] {
 background:white; border:1.5px solid #c8e9ff; border-radius:16px; padding:12px;
}
div.stButton > button {
 border-radius:100px; border:1px solid #b7def8; color:#1686cf;
}
div.stButton > button[kind="primary"] {
 background:linear-gradient(135deg,#56b4f5,#2196e0); border:0; color:white;
}
div[data-testid="stExpander"] {
 background:white; border:1.5px solid #c8e9ff; border-radius:16px;
}
.card {
 background:white; border:1.5px solid #c8e9ff; border-radius:17px;
 padding:14px 16px; margin:8px 0; box-shadow:0 3px 12px rgba(86,180,245,.10);
}
.muted { color:#7a9bb5; font-size:.85rem; }
.pill {
 display:inline-block; padding:3px 9px; border-radius:30px;
 background:#e8f6ff; color:#1686cf; font-size:.78rem; margin:2px 3px 2px 0;
}
hr { border-color:#d7edfc; }
</style>
""", unsafe_allow_html=True)

# Firebase REST database: legacy HTML used /jt/{series,singles,reviews}.
def get_secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default

# 요청하신 기존 관리자 비밀번호와 Firebase 주소를 유지하고,
# 게스트 비밀번호만 pnumis로 변경했습니다.
# 운영 배포에서는 아래 값을 Streamlit Secrets에 등록하는 방식을 권장합니다.
FIREBASE_URL = get_secret(
    "FIREBASE_URL",
    "https://sleepground-fan-web-default-rtdb.asia-southeast1.firebasedatabase.app",
).rstrip("/")
ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD", "sleepground")
GUEST_PASSWORD = get_secret("GUEST_PASSWORD", "pnumis")

def firebase_get():
    if not FIREBASE_URL:
        return None
    try:
        response = requests.get(f"{FIREBASE_URL}/jt.json", timeout=12)
        response.raise_for_status()
        return response.json() or {}
    except requests.RequestException as exc:
        st.warning(f"Firebase 데이터를 불러오지 못했습니다. 이 세션에서는 임시 데이터로 동작합니다. ({exc})")
        return None

def firebase_put(data):
    if not FIREBASE_URL:
        return False
    try:
        response = requests.put(f"{FIREBASE_URL}/jt.json", json=data, timeout=12)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        st.error(f"Firebase 저장에 실패했습니다: {exc}")
        return False

def as_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict) and x.get("id")]
    if isinstance(value, dict):
        return [x for x in value.values() if isinstance(x, dict) and x.get("id")]
    return []

def as_map(items):
    return {item["id"]: item for item in items if item.get("id")}

def save_shared():
    if st.session_state.get("is_admin"):
        payload = {
            "series": as_map(st.session_state.series),
            "singles": as_map(st.session_state.singles),
            "reviews": as_map(st.session_state.reviews),
        }
        if FIREBASE_URL:
            if firebase_put(payload):
                st.toast("공유 데이터가 저장되었습니다.", icon="💾")
        else:
            st.info("Firebase URL이 설정되지 않아 데이터는 현재 세션에서만 유지됩니다.")

def init_data():
    if "data_loaded" in st.session_state:
        return
    data = firebase_get() if FIREBASE_URL else None
    st.session_state.series = as_list(data.get("series")) if data is not None else []
    st.session_state.singles = as_list(data.get("singles")) if data is not None else []
    st.session_state.reviews = as_list(data.get("reviews")) if data is not None else []
    st.session_state.watched = {}
    st.session_state.memos = {}
    st.session_state.data_loaded = True

def uid():
    return "_" + uuid.uuid4().hex[:12]

def member_names(ids):
    return [m["name"] for m in MEMBERS if m["id"] in (ids or [])]

def show_member_tags(ids):
    tags = []
    for m in MEMBERS:
        if m["id"] in (ids or []):
            tags.append(f'<span class="pill" style="color:{m["color"]};background:{m["color"]}22">{m["name"]}</span>')
    return " ".join(tags) if tags else '<span class="muted">출연 멤버 미지정</span>'

def login_screen():
    st.markdown('<div class="hero"><h1>잠뜰 TV 팬 웹 ✨</h1><p>좋아하는 시리즈와 영상을 기록하고 감상을 나눠보세요.</p></div>', unsafe_allow_html=True)
    image_path = Path(__file__).parent / "assets" / "profile.jpg"
    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        if image_path.exists():
            st.image(str(image_path), width=145)
    with st.form("login_form"):
        st.subheader("🔐 팬 웹 입장")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력해 주세요")
        remember = st.checkbox("이 세션에서 로그인 유지", value=True)
        submitted = st.form_submit_button("입장하기 🚀", type="primary", use_container_width=True)
    st.caption("관리자: 편집 및 후기 관리 / 게스트: 콘텐츠 열람 및 시청 체크")
    if submitted:
        if ADMIN_PASSWORD and password == ADMIN_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.is_admin = True
            init_data()
            st.rerun()
        elif GUEST_PASSWORD and password == GUEST_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.is_admin = False
            init_data()
            st.rerun()
        else:
            st.error("비밀번호가 틀렸거나 Secrets 설정이 되어 있지 않습니다.")
    if not ADMIN_PASSWORD or not GUEST_PASSWORD:
        st.warning("배포 전 .streamlit/secrets.toml에 ADMIN_PASSWORD와 GUEST_PASSWORD를 설정해 주세요.")

def series_progress(series):
    total = sum(len(s.get("eps", [])) for s in series)
    done = sum(1 for sid, eps in st.session_state.watched.items() for _, val in eps.items() if val)
    return done, total

def render_series():
    series = st.session_state.series
    c1, c2, c3 = st.columns([1.5, 1, 1])
    with c1:
        query = st.text_input("🔎 시리즈 검색", key="series_query", placeholder="시리즈 이름 또는 설명")
    with c2:
        sort_mode = st.selectbox("정렬", ["기본 순", "가나다 순"])
    with c3:
        only_unfinished = st.checkbox("미완료만 보기")
    done, total = series_progress(series)
    a, b, c = st.columns(3)
    a.metric("등록 시리즈", len(series))
    b.metric("전체 에피소드", total)
    c.metric("시청 완료", done)
    st.progress(done / total if total else 0, text=f"전체 시청 진행률 · {done}/{total}")
    filtered = [s for s in series if query.lower() in (s.get("name","") + " " + s.get("desc","")).lower()]
    if sort_mode == "가나다 순":
        filtered.sort(key=lambda x: x.get("name", ""))
    if only_unfinished:
        filtered = [s for s in filtered if any(not st.session_state.watched.get(s["id"], {}).get(str(i), False) for i in range(len(s.get("eps", []))))]
    if not filtered:
        st.info("조건에 맞는 시리즈가 없습니다.")
    for s in filtered:
        eps = s.get("eps", [])
        sid = s["id"]
        watched = st.session_state.watched.setdefault(sid, {})
        finished = sum(bool(watched.get(str(i))) for i in range(len(eps)))
        with st.expander(f"{s.get('icon','🎬')} {s.get('name','이름 없는 시리즈')}  ·  {finished}/{len(eps)}화 시청", expanded=False):
            st.markdown(f'<div class="muted">{s.get("desc","")}</div>{show_member_tags(s.get("members",[]))}', unsafe_allow_html=True)
            if eps:
                st.caption("에피소드별 시청 체크와 개인 메모를 관리할 수 있습니다.")
                for i, ep in enumerate(eps):
                    cols = st.columns([0.12, 0.65, 0.23])
                    with cols[0]:
                        checked = st.checkbox("완료", value=bool(watched.get(str(i))), key=f"ep_{sid}_{i}", label_visibility="collapsed")
                    if checked != bool(watched.get(str(i))):
                        watched[str(i)] = checked
                    with cols[1]:
                        st.write(f"**{i+1}화.** {ep}")
                    with cols[2]:
                        if st.session_state.is_admin and st.button("삭제", key=f"epdel_{sid}_{i}"):
                            s["eps"].pop(i)
                            st.session_state.watched[sid] = {}
                            st.session_state.memos.pop(sid, None)
                            save_shared()
                            st.rerun()
                    memo = st.text_input("개인 메모", value=st.session_state.memos.get(sid, {}).get(str(i), ""), key=f"memo_{sid}_{i}", placeholder="이 화에 대한 메모")
                    st.session_state.memos.setdefault(sid, {})[str(i)] = memo
            else:
                st.caption("아직 등록된 에피소드가 없습니다.")
            if st.session_state.is_admin:
                with st.form(f"add_ep_{sid}"):
                    new_ep = st.text_input("새 에피소드 제목")
                    if st.form_submit_button("에피소드 추가"):
                        if new_ep.strip():
                            s.setdefault("eps", []).append(new_ep.strip())
                            save_shared()
                            st.rerun()
            if st.session_state.is_admin:
                with st.form(f"edit_series_{sid}"):
                    st.markdown("**시리즈 정보 수정**")
                    new_name = st.text_input("시리즈 이름", value=s.get("name",""))
                    new_desc = st.text_input("설명", value=s.get("desc",""))
                    if st.form_submit_button("정보 수정 저장"):
                        s["name"], s["desc"] = new_name.strip(), new_desc.strip()
                        save_shared()
                        st.rerun()
                if st.button("시리즈 삭제", key=f"delseries_{sid}"):
                    st.session_state.series = [x for x in series if x["id"] != sid]
                    save_shared()
                    st.rerun()
    if st.session_state.is_admin:
        with st.expander("➕ 새 시리즈 등록"):
            with st.form("new_series"):
                name = st.text_input("시리즈 이름 *")
                desc = st.text_input("설명")
                icon = st.selectbox("아이콘", EMOJIS)
                color_name = st.selectbox("대표 색상", [m["name"] for m in MEMBERS], index=4)
                members = st.multiselect("출연 멤버", [m["name"] for m in MEMBERS])
                if st.form_submit_button("시리즈 추가", type="primary"):
                    if not name.strip():
                        st.error("시리즈 이름을 입력해 주세요.")
                    else:
                        color = next(m["color"] for m in MEMBERS if m["name"] == color_name)
                        ids = [m["id"] for m in MEMBERS if m["name"] in members]
                        st.session_state.series.append({"id":uid(),"name":name.strip(),"desc":desc.strip(),"icon":icon,"color":color,"members":ids,"eps":[]})
                        save_shared()
                        st.rerun()

def render_singles():
    singles = st.session_state.singles
    q = st.text_input("🔎 단편 영상 검색", placeholder="영상 제목 또는 메모")
    member_filter = st.multiselect("출연 멤버 필터", [m["name"] for m in MEMBERS])
    status = st.selectbox("시청 상태", ["전체", "시청 완료", "아직 안 봄"])
    filtered = [x for x in singles if q.lower() in (x.get("name","")+" "+x.get("desc","")).lower()]
    if member_filter:
        filtered = [x for x in filtered if set(member_filter).issubset(set(member_names(x.get("members",[]))))]
    if status != "전체":
        filtered = [x for x in filtered if bool(x.get("watched")) == (status == "시청 완료")]
    st.caption(f"검색 결과 {len(filtered)}개 / 전체 {len(singles)}개")
    for item in filtered:
        with st.container(border=True):
            left, right = st.columns([0.78,0.22])
            with left:
                st.markdown(f"### {item.get('icon','🎬')} {item.get('name','')}")
                st.write(item.get("desc",""))
                st.markdown(show_member_tags(item.get("members",[])), unsafe_allow_html=True)
                if item.get("extraPersons"):
                    st.caption("함께 출연: " + ", ".join(item["extraPersons"]))
                st.caption("등록일: " + item.get("date",""))
            with right:
                watched = st.checkbox("시청 완료", value=bool(item.get("watched")), key=f"singlewatched_{item['id']}")
                if watched != bool(item.get("watched")):
                    item["watched"] = watched
                    save_shared() if st.session_state.is_admin else None
                    st.rerun()
                if st.session_state.is_admin and st.button("삭제", key=f"singledel_{item['id']}"):
                    st.session_state.singles = [x for x in singles if x["id"] != item["id"]]
                    save_shared()
                    st.rerun()
    if not filtered:
        st.info("검색 조건에 맞는 단편 영상이 없습니다.")
    if st.session_state.is_admin:
        with st.expander("➕ 단편 영상 등록"):
            with st.form("new_single"):
                name = st.text_input("영상 제목 *")
                desc = st.text_input("메모")
                icon = st.selectbox("아이콘", EMOJIS, key="single_icon")
                color_name = st.selectbox("대표 색상", [m["name"] for m in MEMBERS], index=4, key="single_color")
                members = st.multiselect("출연 멤버", [m["name"] for m in MEMBERS], key="single_members")
                extra = st.text_input("픽셀리 외 출연 인물 (쉼표로 구분)")
                if st.form_submit_button("단편 영상 추가", type="primary"):
                    if not name.strip():
                        st.error("영상 제목을 입력해 주세요.")
                    else:
                        color = next(m["color"] for m in MEMBERS if m["name"] == color_name)
                        ids = [m["id"] for m in MEMBERS if m["name"] in members]
                        st.session_state.singles.insert(0, {"id":uid(),"name":name.strip(),"desc":desc.strip(),"icon":icon,"color":color,"watched":False,"members":ids,"extraPersons":[x.strip() for x in extra.split(",") if x.strip()],"date":date.today().strftime("%Y. %m. %d.")})
                        save_shared()
                        st.rerun()

def render_reviews():
    reviews = st.session_state.reviews
    options = {"전체 후기":"all"}
    options.update({f"📺 {s.get('name','')}":"s_"+s["id"] for s in st.session_state.series})
    options.update({f"🎬 {s.get('name','')}":"v_"+s["id"] for s in st.session_state.singles})
    selected = st.selectbox("후기 분류", list(options.keys()))
    ref = options[selected]
    filtered = reviews if ref == "all" else [r for r in reviews if r.get("refId") == ref]
    st.caption(f"후기 {len(filtered)}개")
    for r in filtered:
        with st.container(border=True):
            top = st.columns([0.8,0.2])
            with top[0]:
                label = f"{r.get('typeLabel','')} · {r.get('label','')}" if r.get("label") else "자유 후기"
                st.markdown(f"**{label}**　{'⭐' * int(r.get('rating',0))}")
            with top[1]:
                if st.session_state.is_admin and st.button("삭제", key=f"reviewdel_{r['id']}"):
                    st.session_state.reviews = [x for x in reviews if x["id"] != r["id"]]
                    save_shared()
                    st.rerun()
            st.write(r.get("text",""))
            st.caption(r.get("date",""))
    if not filtered:
        st.info("아직 작성된 후기가 없습니다.")
    if st.session_state.is_admin:
        with st.expander("✍️ 새 영상 후기 작성"):
            with st.form("new_review"):
                kind = st.selectbox("종류", ["선택 안 함", "시리즈", "단편 영상"])
                item_options = st.session_state.series if kind == "시리즈" else st.session_state.singles if kind == "단편 영상" else []
                item_names = ["선택 안 함"] + [x.get("name","") for x in item_options]
                chosen = st.selectbox("대상 영상", item_names)
                rating = st.slider("별점", 1, 5, 5)
                review_text = st.text_area("후기 내용", placeholder="어떤 영상을 봤나요? 감상을 자유롭게 적어보세요!")
                if st.form_submit_button("후기 저장", type="primary"):
                    if not review_text.strip():
                        st.error("후기 내용을 입력해 주세요.")
                    else:
                        target = next((x for x in item_options if x.get("name") == chosen), None)
                        typelabel = "시리즈" if kind == "시리즈" else "단편" if kind == "단편 영상" else ""
                        prefix = "s_" if kind == "시리즈" else "v_"
                        st.session_state.reviews.insert(0, {"id":uid(),"label":target.get("name","") if target else "","typeLabel":typelabel,"refId":prefix+target["id"] if target else "","text":review_text.strip(),"rating":rating,"date":date.today().strftime("%Y. %m. %d.")})
                        save_shared()
                        st.rerun()

def main():
    if not st.session_state.get("logged_in"):
        login_screen()
        return
    init_data()
    logo = Path(__file__).parent / "assets" / "profile.jpg"
    col1, col2 = st.columns([0.13,0.87])
    with col1:
        if logo.exists():
            st.image(str(logo), width=65)
    with col2:
        role = "🔑 관리자" if st.session_state.is_admin else "👁 게스트"
        st.markdown(f'<div class="hero"><h1>잠뜰 TV 팬 웹 ✨</h1><p>{role} 모드 · 좋아하는 콘텐츠를 기록해 보세요!</p></div>', unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### ⚙️ 계정")
        st.write("현재 모드: " + role)
        if st.button("로그아웃", use_container_width=True):
            for key in ["logged_in","is_admin","data_loaded","series","singles","reviews","watched","memos"]:
                st.session_state.pop(key, None)
            st.rerun()
        st.divider()
        st.caption("관리자만 콘텐츠와 후기를 추가·수정·삭제할 수 있습니다.")
        if not FIREBASE_URL:
            st.warning("Firebase 미설정: 변경 사항은 현재 세션에만 남습니다.")
    series_tab, single_tab, review_tab = st.tabs(["📺 시리즈", "🎬 단편 영상", "✍️ 영상 후기"])
    with series_tab:
        render_series()
    with single_tab:
        render_singles()
    with review_tab:
        render_reviews()
    st.divider()
    st.caption("잠뜰 TV 팬 웹 · Streamlit edition")

if __name__ == "__main__":
    main()
