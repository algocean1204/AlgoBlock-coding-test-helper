# 개발 환경 만들기

이 문서는 저장소를 받아 서버와 창을 띄우고, 안내 데모와 설치 파일을 다시 만드는 방법을 답한다. 시험은 [testing.md](testing.md), 기본 문제 추가는 [add-builtin-problem.md](add-builtin-problem.md), 채점 언어 추가는 [add-language.md](add-language.md)를 본다.

## 준비물

| 항목 | 필요한 곳 | 메모 |
| --- | --- | --- |
| Python 3.12 | 엔진, 서버, 채점기, 검사 도구 | CI는 3.12로만 돈다 |
| uv | 아래 `uv run` 명령 | 저장소에는 requirements나 pyproject 파일이 없다. 패키지는 명령의 `--with`로 정한다 |
| Node.js 20.19 이상 | 안내 데모 빌드 | `app/ui/stageshow/`에서만 쓴다 |
| Chrome | 안내 데모 화면 확인 | 찾지 못하면 `CHROME_PATH`에 실행 파일을 적는다 |
| 채점 언어 도구 | 그 언어로 채점할 때 | 언어별 도구는 [설치와 실행](../guide/install.md#언어-도구)을 본다 |

## 저장소 받기

```bash
git clone https://github.com/algocean1204/AlgoBlock-coding-test-helper
cd AlgoBlock-coding-test-helper
```

## 서버와 창 실행

서버만 띄운다. 뜨면 `AlgoBlock: http://127.0.0.1:8791`을 찍는다. 서버는 127.0.0.1에만 묶인다.

```bash
cd app && uv run --no-project --python 3.12 --with langgraph --with pypdf python ui/server.py
```

창으로 띄운다. 창 모드는 서버를 같은 프로세스에서 띄우고, 서버가 응답할 때까지 최대 10초 기다린다.

```bash
cd app && uv run --no-project --python 3.12 --with langgraph --with pywebview python ui/window.py
```

같은 포트에 서버가 이미 떠 있으면 새로 띄우지 않고 그 화면을 연다.

## 환경 변수

| 변수 | 기본값 | 뜻 |
| --- | --- | --- |
| `ALGOBLOCK_UI_PORT` | `8791` | 서버 포트 |
| `ALGOBLOCK_UI_DATA` | `app/ui/data` | 데이터 폴더(DB, 등록 문제, 블록 코드, 로그인 토큰, 키) |
| `ALGOBLOCK_UI_STATIC` | `app/ui` | 화면 파일 폴더 |
| `ALGOBLOCK_UI_BUILTIN` | `<ALGOBLOCK_UI_STATIC>/builtin.json` | 기본 문제 묶음 파일 |
| `ALGOBLOCK_UI_PREPARE` | `1` | `0`이면 문제를 열 때 미리 만들기를 하지 않고, 모델 목록도 받지 않는다 |
| `ALGOBLOCK_UI_CLIENT` | 없음 | `cli`면 이 PC의 Claude Code(`claude -p`)를 모델로 쓴다. 개발용이다 |
| `ALGOBLOCK_UI_SCENARIOS=1`, `ALGOBLOCK_EVAL_EXTRA` | 없음 | 개발용 예시 문제를 목록에 보인다 |
| `ALGOBLOCK_JUDGE_DIR` | `app/judge` | 채점기 폴더 |
| `ALGOBLOCK_EMBED_DIR` | 아래 순서 참고 | 임베딩 모델 폴더 |
| `ALGOBLOCK_LLM_AUTH_DIR` | `<데이터 폴더>/auth` | ChatGPT 로그인 토큰 폴더 |
| `ALGOBLOCK_LLM_USAGE_LOG` | `<데이터 폴더>/usage.jsonl` | 모델 사용량 기록 파일 |
| `ALGOBLOCK_LLM_TIMEOUT` | `60` | 모델 응답 제한 시간(초) |
| `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` | 없음 | 모델 키. 화면에서 넣을 수도 있다 |

`ALGOBLOCK_LLM_PROVIDER`, `ALGOBLOCK_LLM_MODEL`, `ALGOBLOCK_THEME_<과정>`과 키를 읽는 순서는 [AI 연결](../guide/connect-ai.md)에서 다룬다.

## 선택 기능: 비슷한 문제 찾기

비슷한 문제 찾기는 기기 안의 임베딩 모델 `intfloat/multilingual-e5-small`을 쓴다. 패키지 `qdrant-client`, `onnxruntime`, `tokenizers` 가운데 하나라도 없거나 모델 파일이 없으면 벡터 검색만 꺼지고, 튜터는 온톨로지와 SQLite만으로 돈다. 실행 중에는 모델을 내려받지 않는다.

모델은 표준 라이브러리만 쓰는 명령으로 huggingface.co에서 받는다. 약 250MB다. `model.onnx`와 `tokenizer.json`의 크기와 SHA-256이 다르면 받은 파일을 지우고 멈춘다.

```bash
cd app && python3 tutor/knowledge/embed.py fetch ui/data/models
```

모델 폴더는 `ALGOBLOCK_EMBED_DIR`, 데이터 폴더의 `models`, `app/packaging/models` 순서로 찾는다. 이 기능을 켜려면 서버를 띄울 때 패키지를 더한다.

```bash
cd app && uv run --no-project --python 3.12 --with langgraph --with pypdf --with qdrant-client --with onnxruntime --with tokenizers python ui/server.py
```

## 폴더 구성

| 폴더 | 하는 일 |
| --- | --- |
| `app/ui/` | 화면(HTML·JS·CSS), 로컬 서버, 창, 기본 문제와 케이스 도구 |
| `app/tutor/` | LangGraph 튜터 엔진. 에이전트마다 폴더 하나 |
| `app/judge/` | 채점기. 7개 언어 실행기와 형 모델 |
| `app/llm/` | 모델 공급자 연결(Claude API 키, OpenAI API 키, ChatGPT 로그인)과 사용량 기록 |
| `app/packaging/` | 설치 파일 만들기 |
| `Docs/` | 공개 문서(guide, architecture, contributing) |
| `.github/` | CI 설정과 기여·보안 안내 |

구조와 구성 요소 사이의 흐름은 [architecture/overview.md](../architecture/overview.md)에 있다.

## 안내 데모 다시 빌드

안내 데모는 `app/ui/stageshow/`의 소스에서 `app/ui/tour-demos.js`와 `app/ui/tour-demos.css`를 만든다. 앱은 이 두 파일만 쓴다.

```bash
cd app/ui/stageshow
npm install
npm run typecheck && npm run build
```

두 결과 파일을 함께 바꾼다. 화면에서 확인하는 방법은 [stageshow README](../../app/ui/stageshow/README.md)를 본다.

## 설치 파일 만들기

| 스크립트 | 실행 환경 | 결과 |
| --- | --- | --- |
| `sh app/packaging/build_mac.sh` | macOS | `app/packaging/dist/AlgoBlock-<버전>-<아키텍처>.dmg`와 `AlgoBlock-macos-<아키텍처>.dmg` |
| `powershell -ExecutionPolicy Bypass -File app\packaging\build_win.ps1` | Windows PC | `app\packaging\dist\AlgoBlock.exe`와 `AlgoBlock-windows-x64.exe` |
| `sh app/packaging/build_win_docker.sh` | macOS·Linux(Docker 필요) | `app/packaging/dist-win/AlgoBlock.exe`와 `AlgoBlock-windows-x64.exe` |

세 스크립트 모두 `uv`(Docker 경로는 Docker와 `python3`)가 있어야 하고, 임베딩 모델을 `app/packaging/models`에 받아 함께 묶는다. macOS 설치 파일은 서명하지 않는다. 버전은 `VERSION` 환경 변수로 정하며 기본값은 `0.1.0`이다(`build_mac.sh`만 쓴다). 자세한 내용은 [packaging README](../../app/packaging/README.md)를 본다.

## 알려진 한계

- Python은 3.12로만 확인했다. 코드가 `X | None` 문법을 쓰므로 3.10 미만에서는 돌지 않는다.
- Windows 실행 파일은 Windows PC에서 `build_win.ps1`로 만드는 것이 정식 경로다. Docker 경로는 Wine에서 빌드하므로 창(WebView2) 동작을 확인하지 못한다.
