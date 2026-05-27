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
# 콘텐츠 구조 정의
#   - 교과별 폴더명, 파일 접두어
#   - 챕터: 공통(주제 1~4), 일반고(주제 1~12)
#   - 주제 제목은 아래 TOPIC_TITLES 에서 자유롭게 수정 가능
# ──────────────────────────────────────────────────────────────────────────
SUBJECTS = {
    "수학": {"folder": "math", "prefix": "ma"},
    "과학": {"folder": "science", "prefix": "sc"},
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
        f'style="width:100%; height:{height}px; border:1px solid #e0e0e0; '
        f'border-radius:8px;" sandbox="allow-scripts allow-same-origin '
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
    st.session_state["jump"] = True


# ──────────────────────────────────────────────────────────────────────────
# 사이드바 — 검색 + 선택 UI
# ──────────────────────────────────────────────────────────────────────────
st.sidebar.title("📘 교과 콘텐츠")

# ── 검색 영역 ────────────────────────────────────────────────────────────
st.sidebar.subheader("🔍 본문 검색")
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
# 검색 결과 클릭으로 넘어온 값이 있으면 위젯 기본값으로 사용
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

iframe_height = st.sidebar.slider("화면 높이(px)", 400, 1400, 800, step=50)

# ──────────────────────────────────────────────────────────────────────────
# 메인 — 콘텐츠 렌더링
# ──────────────────────────────────────────────────────────────────────────
st.markdown(
    f"### {subject} · {chapter}. {CHAPTERS[chapter]['name']} · "
    f"{topic_label(subject, chapter, topic)}"
)

path = build_path(subject, chapter, topic)

if path.exists():
    render_html_file(path, height=iframe_height)
else:
    st.warning(f"콘텐츠 파일을 찾을 수 없습니다: `{path.relative_to(BASE_DIR)}`")
    st.caption("파일이 아직 준비되지 않았거나 경로가 다를 수 있습니다.")

st.sidebar.markdown("---")
st.sidebar.caption(f"불러오는 파일: `{path.relative_to(BASE_DIR)}`")
