import base64
import html
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# ──────────────────────────────────────────────────────────────────────────
# 기본 설정
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="교과 콘텐츠 뷰어", page_icon="📘", layout="wide")

BASE_DIR = Path(__file__).parent

# ──────────────────────────────────────────────────────────────────────────
# 전역 스타일
# ──────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
      /* 메인 영역 상단 여백 줄이기 */
      .block-container { padding-top: 1.8rem; padding-bottom: 2rem; max-width: 1200px; }

      /* 콘텐츠 헤더 배너 (높이 축소) */
      .content-header {
        border-radius: 12px;
        padding: 13px 22px;
        margin-bottom: 16px;
        color: #fff;
        box-shadow: 0 3px 12px rgba(0,0,0,0.08);
      }
      .content-header .eyebrow {
        font-size: 0.78rem; font-weight: 600; letter-spacing: 0.03em;
        opacity: 0.92; margin-bottom: 2px;
      }
      .content-header .title {
        font-size: 1.2rem; font-weight: 700; line-height: 1.25; margin: 0;
      }
      .content-header .meta {
        margin-top: 3px; font-size: 0.78rem; opacity: 0.85;
      }

      /* 홈 히어로 */
      .hero {
        border-radius: 16px;
        padding: 32px 34px;
        margin-bottom: 22px;
        background: linear-gradient(135deg, #5566e0, #8a6cf0 55%, #1aa179);
        color: #fff;
        box-shadow: 0 6px 20px rgba(0,0,0,0.10);
      }
      .hero h1 { font-size: 1.7rem; font-weight: 800; margin: 0 0 6px 0; }
      .hero p  { font-size: 0.95rem; opacity: 0.92; margin: 0; }

      /* 통계 카드 */
      .stat-card {
        border-radius: 14px; padding: 18px 20px; height: 100%;
        background: #fff; border: 1px solid #ececf3;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
      }
      .stat-card .num { font-size: 1.9rem; font-weight: 800; line-height: 1; }
      .stat-card .lbl { font-size: 0.82rem; color: #6b7280; margin-top: 6px; }

      /* 교과 카드 */
      .subject-card {
        border-radius: 14px; padding: 20px 22px; color: #fff;
        box-shadow: 0 3px 12px rgba(0,0,0,0.08); margin-bottom: 6px;
      }
      .subject-card .sc-icon { font-size: 1.6rem; }
      .subject-card .sc-name { font-size: 1.15rem; font-weight: 700; margin: 4px 0 10px 0; }
      .subject-card .sc-stat { font-size: 0.82rem; opacity: 0.9; }
      /* 진도 바 */
      .pbar { background: rgba(255,255,255,0.28); border-radius: 6px; height: 8px; margin: 8px 0 4px; }
      .pbar > div { background: #fff; border-radius: 6px; height: 8px; }

      /* 사이드바 */
      section[data-testid="stSidebar"] { background: #f7f8fc; }
      section[data-testid="stSidebar"] .sb-brand {
        font-size: 1.15rem; font-weight: 800; color: #3b3f5c;
        padding: 4px 0 2px; margin-bottom: 2px;
      }
      section[data-testid="stSidebar"] .sb-sub {
        font-size: 0.72rem; color: #8b90a8; margin-bottom: 10px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────
# 콘텐츠 구조 정의
#   - 교과별 폴더명, 파일 접두어
#   - 챕터: 공통(주제 1~4), 일반고(주제 1~12)
#   - 주제 제목은 아래 TOPIC_TITLES 에서 자유롭게 수정 가능
# ──────────────────────────────────────────────────────────────────────────
SUBJECTS = {
    "수학": {"folder": "math", "prefix": "ma",
             "icon": "📐", "color": "#4f6df5", "color2": "#7c94ff"},
    "과학": {"folder": "science", "prefix": "sc",
             "icon": "🔬", "color": "#1aa179", "color2": "#46c79d"},
}

CHAPTERS = {
    1: {"name": "공통", "n_topics": 4},
    2: {"name": "일반고", "n_topics": 12},
}

# 화면에 보여줄 주제 제목. 비워두면 "주제 N" 으로 자동 표시됩니다.
# 예) TOPIC_TITLES["수학"][1][1] = "함수의 정의"
TOPIC_TITLES = {
    "수학": {1: {}, 2: {}},
    "과학": {1: {}, 2: {}},
}


def topic_label(subject: str, chapter: int, topic: int) -> str:
    custom = TOPIC_TITLES.get(subject, {}).get(chapter, {}).get(topic)
    return f"주제 {topic}. {custom}" if custom else f"주제 {topic}"


def build_path(subject: str, chapter: int, topic: int) -> Path:
    info = SUBJECTS[subject]
    fname = f"{info['prefix']}_{chapter}_{topic}.html"
    return BASE_DIR / info["folder"] / fname


def render_html_file(path: Path, height: int = 800):
    """로컬 HTML 파일을 iframe(srcdoc)으로 렌더링."""
    html_text = path.read_text(encoding="utf-8")
    # 안전하게 srcdoc 으로 직접 주입 (별도 서버 없이 동작)
    encoded = base64.b64encode(html_text.encode("utf-8")).decode("utf-8")
    iframe = (
        f'<iframe src="data:text/html;base64,{encoded}" '
        f'style="width:100%; height:{height}px; border:1px solid #e8e8ee; '
        f'border-radius:12px; box-shadow:0 2px 10px rgba(0,0,0,0.05);" '
        f'sandbox="allow-scripts allow-same-origin '
        f'allow-popups allow-forms"></iframe>'
    )
    components.html(iframe, height=height + 20, scrolling=False)


# ──────────────────────────────────────────────────────────────────────────
# 검색 — HTML 본문 텍스트 인덱싱
# ──────────────────────────────────────────────────────────────────────────
def strip_html(raw: str) -> str:
    """HTML 에서 script/style 제거 후 태그를 벗겨 plain text 로 변환."""
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw,
                 flags=re.IGNORECASE | re.DOTALL)
    raw = re.sub(r"<[^>]+>", " ", raw)          # 태그 제거
    raw = html.unescape(raw)                     # &amp; 등 엔티티 복원
    raw = re.sub(r"\s+", " ", raw)               # 공백 정규화
    return raw.strip()


@st.cache_data(show_spinner=False)
def build_search_index() -> list[dict]:
    """모든 교과/챕터/주제 HTML 을 읽어 검색 인덱스를 만든다.
    파일 내용이 바뀌면 캐시를 비워야 하므로 mtime 합계를 키에 섞는다."""
    index = []
    for subject, info in SUBJECTS.items():
        for chapter, cinfo in CHAPTERS.items():
            for topic in range(1, cinfo["n_topics"] + 1):
                path = build_path(subject, chapter, topic)
                if not path.exists():
                    continue
                try:
                    text = strip_html(path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                index.append({
                    "subject": subject,
                    "chapter": chapter,
                    "topic": topic,
                    "label": f"{subject} · {chapter}.{cinfo['name']} · "
                             f"{topic_label(subject, chapter, topic)}",
                    "text": text,
                    "lower": text.lower(),
                })
    return index


def make_snippet(text: str, lower: str, query: str, width: int = 60) -> str:
    """검색어 주변 문맥을 잘라 스니펫으로 반환."""
    pos = lower.find(query.lower())
    if pos == -1:
        return text[:width * 2] + ("…" if len(text) > width * 2 else "")
    start = max(0, pos - width)
    end = min(len(text), pos + len(query) + width)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end]}{suffix}"


def goto_content(subject: str, chapter: int, topic: int):
    """검색 결과 클릭 시 선택 상태를 갱신하고 본문으로 이동."""
    st.session_state["sel_subject"] = subject
    st.session_state["sel_chapter"] = chapter
    st.session_state["sel_topic"] = topic
    st.session_state["view"] = "viewer"


def go_home():
    st.session_state["view"] = "home"


def open_subject(subject: str):
    """홈 화면의 교과 카드에서 해당 교과의 첫 주제를 연다."""
    st.session_state["sel_subject"] = subject
    st.session_state["sel_chapter"] = 1
    st.session_state["sel_topic"] = 1
    st.session_state["view"] = "viewer"


def count_topics(subject: str, chapter: int) -> int:
    return CHAPTERS[chapter]["n_topics"]


@st.cache_data(show_spinner=False)
def content_stats() -> dict:
    """전체/교과별 콘텐츠 통계 (준비된 파일 수 vs 전체 슬롯 수)."""
    total_slots = 0
    total_ready = 0
    per_subject = {}
    for subject in SUBJECTS:
        s_slots = 0
        s_ready = 0
        for chapter, cinfo in CHAPTERS.items():
            for topic in range(1, cinfo["n_topics"] + 1):
                s_slots += 1
                if build_path(subject, chapter, topic).exists():
                    s_ready += 1
        per_subject[subject] = {"slots": s_slots, "ready": s_ready}
        total_slots += s_slots
        total_ready += s_ready
    return {
        "total_slots": total_slots,
        "total_ready": total_ready,
        "n_subjects": len(SUBJECTS),
        "n_topics_per_set": sum(c["n_topics"] for c in CHAPTERS.values()),
        "per_subject": per_subject,
    }


# 첫 진입 시 기본 화면은 홈
if "view" not in st.session_state:
    st.session_state["view"] = "home"



# ──────────────────────────────────────────────────────────────────────────
# 사이드바 — 브랜드 + 홈 버튼 + 검색 + 선택 UI
# ──────────────────────────────────────────────────────────────────────────
st.sidebar.markdown('<div class="sb-brand">📘 AIDT 콘텐츠</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sb-sub">교과 디지털 콘텐츠 뷰어</div>', unsafe_allow_html=True)

st.sidebar.button("🏠 홈 · 대시보드", use_container_width=True, on_click=go_home)

st.sidebar.markdown("---")

# ── 검색 영역 ────────────────────────────────────────────────────────────
st.sidebar.markdown("**🔍 본문 검색**")
query = st.sidebar.text_input("검색어", placeholder="예: 함수, 광합성 …",
                              label_visibility="collapsed")

if query.strip():
    index = build_search_index()
    q = query.strip().lower()
    hits = [item for item in index if q in item["lower"]]

    st.sidebar.caption(f"검색 결과: {len(hits)}건")
    for i, item in enumerate(hits[:50]):
        with st.sidebar.container(border=True):
            st.markdown(f"**{item['label']}**")
            st.caption(make_snippet(item["text"], item["lower"], query))
            st.button(
                "이 콘텐츠 열기",
                key=f"goto_{i}",
                use_container_width=True,
                on_click=goto_content,
                args=(item["subject"], item["chapter"], item["topic"]),
            )
    if len(hits) > 50:
        st.sidebar.caption("결과가 많아 상위 50건만 표시합니다.")

st.sidebar.markdown("---")

# ── 선택 영역 ────────────────────────────────────────────────────────────
st.sidebar.markdown("**📂 콘텐츠 선택**")

subject = st.sidebar.selectbox(
    "교과 선택", list(SUBJECTS.keys()), key="sel_subject"
)

chapter = st.sidebar.radio(
    "챕터 선택",
    options=list(CHAPTERS.keys()),
    format_func=lambda c: f"{c}. {CHAPTERS[c]['name']}",
    key="sel_chapter",
)

n_topics = CHAPTERS[chapter]["n_topics"]

# 챕터가 바뀌어 topic 범위를 벗어나면 보정
if st.session_state.get("sel_topic", 1) > n_topics:
    st.session_state["sel_topic"] = 1

topic = st.sidebar.selectbox(
    "주제(하위모듈) 선택",
    options=list(range(1, n_topics + 1)),
    format_func=lambda t: topic_label(subject, chapter, t),
    key="sel_topic",
)

# 사이드바에서 주제를 직접 고르면 뷰어로 전환하는 버튼
st.sidebar.button("📖 이 콘텐츠 보기", use_container_width=True, type="primary",
                  on_click=lambda: st.session_state.update(view="viewer"))

iframe_height = st.sidebar.slider("화면 높이(px)", 400, 1400, 800, step=50)


# ──────────────────────────────────────────────────────────────────────────
# 메인 — 라우팅: 홈(대시보드) / 뷰어
# ──────────────────────────────────────────────────────────────────────────
def render_home():
    stats = content_stats()

    # 히어로
    st.markdown(
        """
        <div class="hero">
          <h1>📘 AIDT 교과 콘텐츠</h1>
          <p>교과·챕터·주제를 선택하거나, 왼쪽에서 본문을 검색해 바로 콘텐츠를 열 수 있습니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 통계 카드 4종
    c1, c2, c3, c4 = st.columns(4)
    cards = [
        (c1, stats["total_ready"], "준비된 콘텐츠"),
        (c2, stats["total_slots"], "전체 콘텐츠 슬롯"),
        (c3, stats["n_subjects"], "교과 수"),
        (c4, stats["n_topics_per_set"], "교과별 주제 수"),
    ]
    for col, num, lbl in cards:
        col.markdown(
            f'<div class="stat-card"><div class="num">{num}</div>'
            f'<div class="lbl">{lbl}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("####  ")
    st.markdown("##### 교과별 진도")

    # 교과 카드 (진도 바)
    cols = st.columns(len(SUBJECTS))
    for col, (subj, info) in zip(cols, SUBJECTS.items()):
        ps = stats["per_subject"][subj]
        pct = round(ps["ready"] / ps["slots"] * 100) if ps["slots"] else 0
        with col:
            st.markdown(
                f"""
                <div class="subject-card"
                     style="background: linear-gradient(135deg, {info['color']}, {info['color2']});">
                  <div class="sc-icon">{info['icon']}</div>
                  <div class="sc-name">{subj}</div>
                  <div class="sc-stat">준비 {ps['ready']} / {ps['slots']} 개 · {pct}%</div>
                  <div class="pbar"><div style="width:{pct}%;"></div></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.button(f"{subj} 콘텐츠 열기", key=f"open_{subj}",
                      use_container_width=True,
                      on_click=open_subject, args=(subj,))


def render_viewer():
    sinfo = SUBJECTS[subject]
    st.markdown(
        f"""
        <div class="content-header"
             style="background: linear-gradient(135deg, {sinfo['color']}, {sinfo['color2']});">
          <div class="eyebrow">{sinfo['icon']} {subject} · {chapter}. {CHAPTERS[chapter]['name']}</div>
          <p class="title">{topic_label(subject, chapter, topic)}</p>
          <div class="meta">전체 {n_topics}개 주제 중 {topic}번째</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    path = build_path(subject, chapter, topic)
    if path.exists():
        render_html_file(path, height=iframe_height)
    else:
        st.warning(f"콘텐츠 파일을 찾을 수 없습니다: `{path.relative_to(BASE_DIR)}`")
        st.caption("파일이 아직 준비되지 않았거나 경로가 다를 수 있습니다.")

    st.sidebar.markdown("---")
    st.sidebar.caption(f"불러오는 파일: `{path.relative_to(BASE_DIR)}`")


if st.session_state["view"] == "home":
    render_home()
else:
    render_viewer()
