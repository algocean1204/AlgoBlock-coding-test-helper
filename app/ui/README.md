# ui — AlgoBlock 화면

알고리즘 문제를 풀고 채점받는 화면과 그 서버다. 튜터 엔진(`app/tutor`)과 채점기(`app/judge`)를 감싼다.

빌드 단계와 프레임워크가 없다. 앱 본체는 HTML, CSS, JS만 쓰고 외부 CDN을 부르지 않는다. 처음 안내의 움직이는 데모만 미리 빌드한 묶음(`tour-demos.js`, `tour-demos.css`)을 쓴다.

- AI 없이 되는 것: 기본 문제 열기, 직접 풀기, 예시 실행, 직접 입력 실행, 제출과 채점, 힌트, 기본 문제 해설, 학습 보고서, 문제 등록, 체크포인트.
- AI 튜터를 연결하면 더 되는 것: '튜터와 차례로', '튜터의 질문으로', 튜터 해설, 꼬리질문, 이 블록 채우기, 틀린 곳 같이 찾기, 피드백, 등록한 문제의 해설.

## 실행

소스로 돌릴 때는 `app`에서 실행한다.

```bash
cd app
uv run --no-project --python 3.12 --with langgraph --with pypdf python ui/server.py
# 브라우저에서 http://127.0.0.1:8791 을 연다
```

- 주소는 늘 127.0.0.1이다. 포트는 `ALGOBLOCK_UI_PORT`, 데이터 폴더는 `ALGOBLOCK_UI_DATA`로 바꾼다. 기본 데이터 폴더는 `app/ui/data`다.
- `pypdf`는 PDF를 올릴 때만 쓴다.
- 비슷한 문항 찾기를 쓰려면 임베딩 모델 파일을 한 번 받고, 패키지 셋을 더 붙인다. 모델은 기기 안 `multilingual-e5-small` 하나다.

```bash
cd app
python3 tutor/knowledge/embed.py fetch ui/data/models
uv run --no-project --python 3.12 --with langgraph --with pypdf --with qdrant-client --with onnxruntime --with tokenizers python ui/server.py
```

- 패키지나 모델 파일이 없으면 벡터 검색만 꺼진다. 튜터는 온톨로지와 SQLite만으로 돈다.
- 네이티브 창으로 열 때는 `ui/window.py`를 쓴다. 서버를 같이 띄우고 창을 연다. 포트를 이미 다른 서버가 쓰고 있으면 새로 띄우지 않고 그 주소를 연다.

```bash
cd app
uv run --no-project --python 3.12 --with langgraph --with pypdf --with pywebview python ui/window.py
```

설치 파일(macOS `.dmg`, Windows `.exe`)을 만드는 법은 [packaging/README.md](../packaging/README.md)에 있다.

## 시험

시험은 모델을 부르지 않는다. 키가 없어도 된다.

```bash
cd app
uv run -q --no-project --python 3.12 --with langgraph --with pypdf python -B ui/test_server.py
python3 -B ui/test_structure.py   # 저장소 구조
python3 -B ui/test_publish.py     # 공개 전 검사(키, 개인 경로, 내부 이름, 큰 파일, 링크)
```

`test_server.py`는 unittest가 아니다. `main()`이 확인 함수를 차례로 부르고, 끝에 `ok`를 찍는다.

## 화면

- 쓰는 법은 [Docs/guide/solve.md](../../Docs/guide/solve.md), 문제 등록은 [Docs/guide/add-problem.md](../../Docs/guide/add-problem.md), AI 연결과 과정별 모델은 [Docs/guide/connect-ai.md](../../Docs/guide/connect-ai.md)에 있다.
- 문제 화면의 오른쪽 칸은 푸는 방식 셋(`app.js`의 `solo`, `guide`, `chair`)이다: '혼자 풀기', '튜터와 차례로', '튜터의 질문으로'. '혼자 풀기' 안에 '힌트'와 '해설' 탭이 있다. AI가 연결되지 않으면 '혼자 풀기'만 쓴다.
- 처음 안내의 데모 묶음을 다시 빌드하는 법은 [stageshow/README.md](stageshow/README.md)에 있다. 기본 문제를 더하거나 고치는 법은 [problems/README.md](problems/README.md)에 있다.

## 파일

| 파일 | 하는 일 |
| --- | --- |
| `server.py` | 표준 라이브러리 HTTP 서버. 정적 파일과 `/api/*`만 낸다 |
| `window.py` | 서버를 같이 띄우고 네이티브 창으로 연다 |
| `updater.py` | 새 버전 확인(켤 때와 24시간마다, 실패하면 1시간부터 두 배씩 최대 6시간 간격으로 다시)과 업데이트(받기, SHA-256 확인, 묶인 macOS 앱(`swap.sh`)과 Windows exe(`swap.ps1`)의 바꿔 끼우기와 되돌리기). 앱의 버전(`VERSION`)과 Windows 릴리스 파일 이름(`WINDOWS_ASSET`)도 여기 있다 |
| `index.html`, `app.css`, `app.js` | 화면. 상태를 바꾸고, 서버에 요청하고, 다시 그린다. 처음 안내는 `index.html`의 `<dialog id="tour">`와 `app.js`의 `TOUR`, `renderTour`, `openTour`다 |
| `builtin.json` | 기본 문제 묶음(75문제). 빌드 결과물이라 손으로 고치지 않는다 |
| `make_builtin.py` | `problems/`의 문제 폴더를 `builtin.json`으로 묶는다 |
| `problemkit.py` | 문제 폴더 읽기, 케이스 만들기, 검사(`check`, `stub`, `try`) |
| `casegen.py` | 효율성 케이스의 큰 입력을 다시 만드는 난수 |
| `casemake.py` | 등록한 문제의 숨은 케이스 만들기. 정답 풀이·단순 풀이·생성기를 채점기로 대조한다. 모델을 부르지 않는다 |
| `stubs.py` | 언어별 시작 코드와 표준 입출력 문제의 main 뼈대 |
| `problems/` | 기본 문제의 원본 폴더(주제 15개 × 5단계) |
| `stageshow/` | 처음 안내 데모의 소스와 빌드 |
| `tour-demos.js`, `tour-demos.css` | 처음 안내 데모의 미리 빌드한 묶음 |
| `PretendardVariable.woff2`, `PretendardVariable-LICENSE.txt` | 맥 밖에서 쓰는 글꼴과 그 라이선스(SIL OFL 1.1). 맥은 시스템 글꼴을 쓴다 |
| `icon.svg`, `favicon.svg` | 앱 아이콘과 파비콘 |
| `test_server.py`, `test_update.py`, `test_structure.py`, `test_publish.py` | 화면 서버 시험, 업데이트 시험(`test_server.py`가 부른다), 저장소 구조 시험, 공개 전 검사 |
| `data/` | 사용자 데이터 폴더. git에서 빠진다. 들어 있는 파일은 [Docs/architecture/data.md](../../Docs/architecture/data.md)에 있다 |

## 서버 API

모든 API는 POST와 JSON이다. PUT, DELETE, PATCH, OPTIONS, TRACE, CONNECT는 405다. GET은 정적 파일과 올린 원본만 낸다.

GET

| 경로 | 설명 |
| --- | --- |
| `/`, `/index.html`, `/app.css`, `/app.js`, `/icon.svg`, `/favicon.svg`, `/tour-demos.js`, `/tour-demos.css`, `/PretendardVariable.woff2` | 정적 파일 |
| `/asset/<문제 id>/<번호>` | 등록할 때 올린 원본. 등록한 문제만 된다. `X-Content-Type-Options: nosniff` |

POST, 문제와 무관한 것 16개

| 경로 | 설명 |
| --- | --- |
| `/api/problems` | 목록과 주제별 진행. 오늘 출석을 찍는다 |
| `/api/report` | 학습 보고서(모델 0회) |
| `/api/problems/new` | 문제 등록 |
| `/api/problems/edit` | 등록한 문제 고치기 |
| `/api/problems/delete` | 등록한 문제와 그 기록 지우기 |
| `/api/problems/read` | 올린 파일에서 글 읽기(저장하지 않는다) |
| `/api/problems/cases` | 입출력 예 표나 예제 구역에서 케이스 찾기(모델 0회) |
| `/api/tools` | 언어 도구 있음·없음. `refresh: true`면 다시 센다 |
| `/api/accounts` | 연결 상태, 키 있음, 과정별 급과 모델 이름, 주제 목록, 마지막 언어, `tour_seen`, 칸 너비 `panes` |
| `/api/tour` | 처음 안내를 봤다고 적는다 |
| `/api/prefs` | 문제·코드·튜터 칸의 너비 몫 `panes`(수 셋, 각각 5에서 90, 합 100)를 저장한다. `null`이면 기본 배치 |
| `/api/theme` | 과정 하나의 급과 추론 정도를 저장한다(빈 값은 기본값) |
| `/api/client` | 연결 방식 바꾸기(`cli` 또는 `provider`) |
| `/api/key` | API 키 넣기(400자까지) |
| `/api/chatgpt/login` | ChatGPT 로그인 주소 받기 |
| `/api/update` | 새 버전. `action`: `status`, `check`, `auto`(`on`), `skip`, `download`, `install`, `reveal`. 거절은 409 |

POST, 문제 하나에 대한 것 19개. 본문에 `id`가 필요하다.

| 경로 | 설명 |
| --- | --- |
| `/api/state` | 문제 화면 상태. 등록한 문제는 `open: true`면 뒤에서 튜터 준비를 시작한다(기본 문제는 튜터를 시작할 때 준비한다) |
| `/api/language` | 풀이 언어 바꾸기. 계획, 대화, 블록 진행을 지우고 코드는 언어마다 보관한다 |
| `/api/run` | 공개 예시만 실행하거나 `input` 하나를 직접 실행한다. 제출로 남기지 않는다 |
| `/api/hint` | 다음 힌트 하나(`peek: true`면 본 것만 다시 보여 준다) |
| `/api/solution` | 해설. 기본 문제는 실린 해설, 등록한 문제는 튜터가 만든 풀이 가이드. 통과 전이면 409, `force: true`면 연다 |
| `/api/code` | 직접 풀기 코드 저장 |
| `/api/blocks` | 블록 칸 코드 저장 |
| `/api/compose` | 블록 칸 코드를 블록 코드 확인과 같은 방식으로 모은다 |
| `/api/checkpoint` | 지금 언어의 체크포인트 덮어쓰기 |
| `/api/checkpoint/restore` | 코드 칸만 되돌리기 |
| `/api/reset` | 이 문제를 처음부터 |
| `/api/submit` | 모든 케이스로 채점하고 제출로 남긴다 |
| `/api/feedback/get` | 저장된 피드백 |
| `/api/turn` | '튜터의 질문으로'나 '튜터와 차례로'의 한 턴 |
| `/api/followup` | 꼬리질문 |
| `/api/fill` | 이 블록 채우기 |
| `/api/explain` | 튜터 해설 |
| `/api/feedback` | 피드백 만들기 |
| `/api/debug` | 틀린 곳 같이 찾기(코드가 바뀌었으면 다시 채점한다) |

## 요청 검사

화면 서버는 이 기기 안에서만 연다. 다른 사이트가 이 서버를 부르지 못하게 다음을 검사한다(`Handler._local`, `Handler._refused`). 보안 전체는 [Docs/architecture/security.md](../../Docs/architecture/security.md)에 있다.

- GET과 POST 모두 Host가 `127.0.0.1` 또는 `localhost`(포트는 상관없다)여야 한다. 아니면 403이다.
- POST는 본문을 읽기 전에 본다. Content-Type이 정확히 `application/json`이어야 한다(아니면 415). Origin이 있으면 이 서버의 주소여야 한다. Sec-Fetch-Site가 있으면 `same-origin` 또는 `none`이어야 한다(아니면 403).
- 본문 상한은 1,000,000바이트다. 파일을 싣는 세 경로(`/api/problems/read`, `/new`, `/edit`)는 60,000,000바이트다. 넘으면 413이다.
- 깨진 JSON이나 객체가 아닌 본문은 400이다. 모든 응답에 `Cache-Control: no-store`를 붙인다.

## 환경 변수

| 변수 | 뜻 | 기본값 |
| --- | --- | --- |
| `ALGOBLOCK_UI_PORT` | 서버 포트. 주소는 늘 127.0.0.1 | 8791 |
| `ALGOBLOCK_UI_DATA` | 데이터 폴더 | `app/ui/data` |
| `ALGOBLOCK_UI_STATIC` | 화면 파일 폴더 | `app/ui` |
| `ALGOBLOCK_UI_BUILTIN` | 기본 문제 묶음 파일 | `ALGOBLOCK_UI_STATIC`의 `builtin.json` |
| `ALGOBLOCK_UI_CLIENT` | `cli`면 이 PC의 Claude Code(`claude -p`)를 모델로 쓴다(개발용) | 연결한 공급자 |
| `ALGOBLOCK_UI_PREPARE` | 0이면 미리 만들기를 끈다 | 1 |
| `ALGOBLOCK_UI_SCENARIOS` | 1이면 예시 시나리오 문제를 목록에 보인다(개발용) | 끔 |
| `ALGOBLOCK_EVAL_EXTRA` | 평가용 문제 JSON 폴더. 주면 그 문제도 목록에 보인다(개발용) | 없음 |
| `ALGOBLOCK_JUDGE_DIR` | 채점기 폴더(`judge.py`가 있는 곳). 묶은 앱에서는 `packaging/launcher.py`가 넘긴다 | `app/judge` |
| `ALGOBLOCK_EMBED_DIR` | 임베딩 모델 폴더(`model.onnx`, `tokenizer.json`). 찾는 순서: 이 변수, 데이터 폴더의 `models`, `app/packaging/models` | 없음 |
| `ALGOBLOCK_LLM_PROVIDER` | 공급자 강제(`claude`, `chatgpt`, `openai`) | 없음 |
| `ALGOBLOCK_LLM_MODEL` | 모든 과정을 한 모델로 쓴다(개발·측정용) | 없음 |
| `ALGOBLOCK_THEME_<과정>` | `모델:정도`로 과정 하나를 정한다(측정용. 예전 이름 `INGEST`는 문제 넣기 세 과정, `EXPLAIN`은 해설·피드백) | 없음 |
| `ALGOBLOCK_LLM_TIMEOUT` | 모델 응답 제한(초) | 60 |
| `ALGOBLOCK_LLM_AUTH_DIR` | 로그인 토큰 폴더 | 데이터 폴더의 `auth` |
| `ALGOBLOCK_LLM_USAGE_LOG` | 모델 호출마다 토큰 수 한 줄을 적는 파일(글과 키는 적지 않는다) | 데이터 폴더의 `usage.jsonl` |

## 알려진 한계

제출 코드를 격리하지 않는 것과 채점 시간 제한의 한계는 [Docs/architecture/judge.md](../../Docs/architecture/judge.md)와 [Docs/architecture/security.md](../../Docs/architecture/security.md)에 있다.

## 디자인

- 색은 `app.css` 맨 위 `:root`의 토큰 이름으로만 쓴다. 바탕 `--bg`(#F5F5F7), 면 `--surface`(#FFFFFF), 강조 `--accent`(#0071E3) 하나, 글 `--text`(#1D1D1F). 블록 종류 색(`--k-*`)은 기호에만 쓴다. 밝은 화면과 어두운 화면을 모두 지원한다. 어두운 값은 `:root[data-scheme="dark"]` 한 블록에 있고, `<head>`의 작은 스크립트가 첫 그림 전에 `<html data-scheme>`을 `light`나 `dark`로 정한다(지금은 운영체제 설정을 따른다).
- 글꼴은 맥에서 시스템 글꼴(`-apple-system`)을 먼저 쓰고, 그 밖에서는 `PretendardVariable.woff2`를 쓴다(`@font-face`).
- 아이콘은 Phosphor Icons bold(MIT, phosphoricons.com) 한 벌이다. `index.html`의 `<symbol>`로 들어 있다.
- 글꼴 라이선스는 SIL Open Font License 1.1이다. 전문은 `PretendardVariable-LICENSE.txt`에 있다.
