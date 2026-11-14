# app

AlgoBlock의 코드다. 전체 그림은 [Docs/architecture/overview.md](../Docs/architecture/overview.md), 실행과 시험은 [Docs/contributing/dev-setup.md](../Docs/contributing/dev-setup.md)에 있다.

| 폴더 | 내용 | 안내 |
| --- | --- | --- |
| `ui/` | 화면 서버(`server.py`, 표준 라이브러리 HTTP)와 화면(`index.html`, `app.js`, `app.css`), 앱 창(`window.py`), 기본 문제(`problems/`)와 그 묶음(`builtin.json`) | [ui/README.md](ui/README.md) |
| `tutor/` | 튜터 엔진(LangGraph). 시험은 `tutor/tests/` | [tutor/README.md](tutor/README.md) |
| `judge/` | 채점기(Python, Java, JavaScript, C++, Go, Kotlin, Rust) | [judge/README.md](judge/README.md) |
| `llm/` | 모델 연결(Claude API 키, OpenAI API 키, ChatGPT 로그인) | [llm/README.md](llm/README.md) |
| `packaging/` | 설치 파일 만들기(PyInstaller. macOS dmg, Windows exe) | [packaging/README.md](packaging/README.md) |

사용자 데이터(기본 `ui/data/`)는 git에 올라가지 않는다. 무엇이 저장되는지는 [Docs/architecture/data.md](../Docs/architecture/data.md)에 있다.

`__init__.py`는 저장소 루트에서 모델 연결을 `app.llm`으로 부르게 둔 것이다.
