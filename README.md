# 교과 콘텐츠 뷰어 (Streamlit)

교과 → 챕터 → 주제(하위모듈)를 선택하면 해당 HTML 콘텐츠가 iframe에 렌더링됩니다.

## 폴더 구조

```
edu_app/
├── app.py
├── requirements.txt
├── math/
│   ├── ma_1_1.html ~ ma_1_4.html      (챕터1: 공통, 주제 1~4)
│   └── ma_2_1.html ~ ma_2_12.html     (챕터2: 일반고, 주제 1~12)
└── science/
    ├── sc_1_1.html ~ sc_1_4.html
    └── sc_2_1.html ~ sc_2_12.html
```

`app.py` 와 `math/`, `science/` 폴더는 **같은 위치**에 두면 됩니다.

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 주제 제목 바꾸기

`app.py` 상단의 `TOPIC_TITLES` 딕셔너리를 채우면 화면에 한글 제목이 표시됩니다.

```python
TOPIC_TITLES = {
    "수학": {
        1: {1: "함수의 정의", 2: "일차함수", ...},
        2: {1: "...", ...},
    },
    ...
}
```

비워두면 `주제 1`, `주제 2` … 로 자동 표시됩니다.

## 동작 방식

HTML 파일을 읽어 `data:` URI(base64)로 iframe에 직접 주입하므로,
별도 웹서버 없이 Streamlit Cloud / 로컬 어디서든 그대로 동작합니다.
