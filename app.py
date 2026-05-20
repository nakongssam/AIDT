import base64
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
    html = path.read_text(encoding="utf-8")
    # 안전하게 srcdoc 으로 직접 주입 (별도 서버 없이 동작)
    encoded = base64.b64encode(html.encode("utf-8")).decode("utf-8")
    iframe = (
        f'<iframe src="data:text/html;base64,{encoded}" '
        f'style="width:100%; height:{height}px; border:1px solid #e0e0e0; '
        f'border-radius:8px;" sandbox="allow-scripts allow-same-origin '
        f'allow-popups allow-forms"></iframe>'
    )
    components.html(iframe, height=height + 20, scrolling=False)


# ──────────────────────────────────────────────────────────────────────────
# 사이드바 — 선택 UI
# ──────────────────────────────────────────────────────────────────────────
st.sidebar.title("📘 교과 콘텐츠")

subject = st.sidebar.selectbox("교과 선택", list(SUBJECTS.keys()))

chapter = st.sidebar.radio(
    "챕터 선택",
    options=list(CHAPTERS.keys()),
    format_func=lambda c: f"{c}. {CHAPTERS[c]['name']}",
)

n_topics = CHAPTERS[chapter]["n_topics"]
topic = st.sidebar.selectbox(
    "주제(하위모듈) 선택",
    options=list(range(1, n_topics + 1)),
    format_func=lambda t: topic_label(subject, chapter, t),
)

iframe_height = st.sidebar.slider("화면 높이(px)", 400, 1400, 800, step=50)

# ──────────────────────────────────────────────────────────────────────────
# 메인 — 콘텐츠 렌더링
# ──────────────────────────────────────────────────────────────────────────
st.markdown(f"### {subject} · {chapter}. {CHAPTERS[chapter]['name']} · {topic_label(subject, chapter, topic)}")

path = build_path(subject, chapter, topic)

if path.exists():
    render_html_file(path, height=iframe_height)
else:
    st.warning(f"콘텐츠 파일을 찾을 수 없습니다: `{path.relative_to(BASE_DIR)}`")
    st.caption("파일이 아직 준비되지 않았거나 경로가 다를 수 있습니다.")

st.sidebar.markdown("---")
st.sidebar.caption(f"불러오는 파일: `{path.relative_to(BASE_DIR)}`")
