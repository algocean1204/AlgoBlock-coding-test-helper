# 시험 돌리기

이 문서는 어떤 시험을 돌릴지, 시험이 무엇을 보는지, CI가 무엇을 돌리는지 답한다. 시험은 모델을 부르지 않으며 API 키가 필요 없다.

## 시험 명령

명령은 저장소 루트에서 시작한다.

```bash
# 1. 튜터 엔진
cd app && uv run -q --no-project --python 3.12 --with langgraph --with pypdf python -B -m unittest discover -s tutor/tests -t .

# 2. 화면 서버 (끝에 ok가 찍히면 통과)
cd app && uv run -q --no-project --python 3.12 --with langgraph --with pypdf python -B ui/test_server.py

# 3. 저장소 구조와 공개 전 검사
cd app && python3 -B ui/test_structure.py
cd app && python3 -B ui/test_publish.py
cd app && python3 -B ui/test_publish.py history

# 4. 채점기 (cd app/judge 에서)
cd app/judge && python3 -B -m unittest test_check
```

| 시험 | 보는 것 |
| --- | --- |
| 1. 튜터 엔진 | 모델 연결, ChatGPT 로그인(네트워크 없이), 설계 경계, 규칙, 평가기, 벡터 색인, 문제 읽기, 온톨로지, 질문 유형 표, 가짜 모델로 돌리는 그래프 흐름과 튜터 서비스 전체(SQLite) |
| 2. 화면 서버 | 등록, 묶음, 효율성 제한, 기본 문제, 학습 보고서, 준비도(이력 표와 시드 고정 무작위 불변식), 홈, 디버그, 고치기·지우기, 시작 코드, 숨은 케이스, 잘못된 HTTP 요청 거르기, 파일 올리기, 화면 파일(글꼴 포함) 존재 |
| 3. 저장소 구조 | 루트·`app`·`Docs`에 허용되지 않은 것이 없는지, 내부 파일이 추적되지 않는지 |
| 3. 공개 전 검사 | 추적하는 파일의 내부 경로, 키 모양의 글자, 개인 경로와 이메일, 내부 이름, 50MB를 넘는 파일, `.env.example`의 키 이름과 서버 키 이름이 같은지, LICENSE, 공개 문서의 링크 |
| 3. 공개 전 검사 `history` | 현재 브랜치의 모든 커밋의 모든 파일에서 내부 경로와 내용(키 모양, 개인 경로·이메일, 내부 이름)을 본다. 걸리면 경로와 커밋 수를 내고 종료 코드 1로 끝난다 |
| 4. 채점기 | 비교, 모드 정하기, 7개 언어의 두 모드, 실패 종류, 다른 모드로 다시 돌리기, 큰 인자 파일, 출력·메모리 상한, 자식 프로세스 정리, CPU 시간 상한, 비밀 환경 변수 거르기, 효율성 케이스. Windows에서는 작업 객체(정상 종료 뒤의 자식, 커밋 메모리 상한과 그때의 `memory_limit` 판정, 프로세스 수 상한, 자식의 오류 창 끄기, 작업 없이 돌 때의 `warning`)도 본다. 다른 OS에서는 그 시험을 건너뛴다 |

- 1번은 임베딩 패키지나 모델 파일이 없으면 색인 시험 일부를 건너뛴다.
- 4번은 기기에 없는 언어를 건너뛴다. 모든 언어를 시험하려면 그 언어의 도구를 먼저 깐다([언어 도구](../guide/install.md#언어-도구)).
- `ALGOBLOCK_LIVE=1`을 주면 실제 모델을 부르는 `tutor/tests/test_live.py`가 돈다. 키가 필요하다. 평소 실행과 CI에서는 건너뛴다.

## 기본 문제 검사

기본 문제 검사는 시험 명령이 아니다. 문제 하나나 주제 하나를 검사하며 모델을 부르지 않는다. 자세한 내용은 [add-builtin-problem.md](add-builtin-problem.md)를 본다.

```bash
cd app && python3 ui/problemkit.py check ui/problems/<주제>
```

전체 검사는 느린 풀이가 시간 초과할 때까지 기다려 수십 분이 걸린다. 그래서 CI에서 돌리지 않는다.

## 바꾼 곳별로 돌릴 것

| 바꾼 곳 | 돌릴 것 |
| --- | --- |
| `app/tutor/` | 1번 |
| `app/llm/` | 1번 |
| `app/ui/` (서버, 화면, 도구) | 2번. 튜터 코드도 건드렸다면 1번 |
| `app/judge/` | 4번과 2번(서버가 채점기를 부른다) |
| `app/ui/problems/` 또는 `problemkit.py`·`make_builtin.py` | 기본 문제 검사(바꾼 주제 폴더) + 2번 |
| 파일이나 폴더를 추가·옮김, `.gitignore` | 3번 `test_structure.py` |
| 공개 문서, 링크, `LICENSE`, `.env.example` | 3번 `test_publish.py` |
| 커밋을 만들거나 고쳤음(푸시 전) | 3번 `test_publish.py history` |

## 시험 정책

- 새 시험은 그 변경을 되돌리면 실패해야 한다. 변경을 임시로 되돌려 시험이 실패하는지 확인한다.
- 시험은 모델을 부르지 않는다(`ALGOBLOCK_LIVE` 시험 제외). 모델이 필요한 동작은 가짜 모델로 시험한다.
- 화면 서버 시험은 API 키 환경 변수를 지우고, 임시 데이터 폴더와 임시 기본 문제 묶음을 쓴다. `ui/builtin.json`은 건드리지 않는다.

## CI

파일은 `.github/workflows/ci.yml`이다. pull request에서만 돈다(열기, 새 커밋, 다시 열기, 초안을 검토 준비로 바꾸기). 푸시에는 돌지 않는다. 같은 PR의 이전 실행은 취소된다. 문서만 바뀐 PR(맨 위·`.github`의 `.md`, `Docs/`, `.github`의 그림·이슈 양식, `LICENSE`)과 초안 PR에서는 엔진·채점기·Windows 시험을 건너뛴다.

| 작업 | 돌리는 것 | 제한 시간 |
| --- | --- | --- |
| `changes` | 바뀐 파일이 문서뿐인지 본다. 목록을 읽지 못하면 모두 돌린다 | 5분 |
| `engine-tests` | 1번, 2번 | 20분 |
| `judge-tests` | 4번(러너에 있는 언어만 돈다) | 20분 |
| `windows` | Windows 러너(`windows-latest`)에서 아래 차례로 돈다 | 60분 |
| `publish-check` | 3번 세 가지(구조, 현재 파일, 모든 커밋) | 10분 |
| `secret-scan` | gitleaks로 기록 전체 검사 | 10분 |
| `branch-name` | 이 저장소 안에서 올린 PR의 브랜치 이름이 규칙에 맞는지 본다. 다른 저장소의 PR, dependabot 브랜치, `develop` → `main` PR은 보지 않는다 | 5분 |
| `ci-passed` | 위 작업이 모두 성공했는지 본다. 건너뛴 작업은 문서만 바뀌었거나 초안일 때만 통과로 친다 | 5분 |

- `develop`·`main` 보호 규칙이 요구하는 검사는 `ci-passed`와 PR 제목 검사 `pr-title`(`.github/workflows/pr-title.yml`)이다. `main`은 `main-source`(`.github/workflows/main-source.yml`)도 요구한다: PR이 이 저장소의 `develop`에서 왔는지, `app/ui/updater.py`의 `VERSION`이 `0.x.y` 꼴이고 지금 `main`의 버전과 마지막 릴리스보다 큰지 본다. 새 검사 작업은 `ci-passed`의 `needs`에 넣는다.

`windows` 작업이 하는 일:

1. 파이썬 패키지를 깔고 Java 17을 PATH 앞에 둔다. 임베딩 모델을 받는다. 모델은 `actions/cache`에 두고, 키는 `embed.py`의 해시다. 캐시에서 꺼낸 파일도 SHA-256을 다시 견준다.
2. 4번(채점기) 시험. 러너에 있는 언어만 돈다. 먼저 언어 도구가 있는지 찍는다. Windows 전용 시험(작업 객체)이 여기서 돈다.
3. 1번(엔진)과 2번(화면 서버) 시험. 모델이 있으면 임베딩 시험도 돈다.
4. 임베딩 색인 시간을 잰다. 모델을 올리는 시간과 기본 문제 글 75개를 넣는 시간을 작업 요약에 적는다. 기준값은 두지 않는다.
5. 서버를 소스(`python ui/server.py`)로 띄워 기본 문제 하나(`builtin.json`의 첫 문제)에 실린 Python 풀이를 `Invoke-RestMethod`로 제출한다. 통과(`ok`)와, 실행 제한을 걸지 못했다는 알림(`notice`)이 없는지 본다. 모델은 부르지 않는다.
6. `build_win.ps1`로 exe를 빌드한다. 해시 파일 `SHA256SUMS-windows-x64`도 만든다.
7. 빌드한 exe를 `--server`로 띄워 5와 같이 제출한다.
8. 업데이트의 바꿔 끼우기를 빌드한 exe의 사본 둘(수정 시각만 다르다)로 끝까지 본다(`python ui/test_update.py exe <exe>`). 성공: 옛 앱이 끝나면 새 exe로 바꿔 열고, 새 앱의 `/`가 200을 준다. 되돌리기: 새 앱의 포트를 막아 응답하지 않게 하면 새 앱을 끝내고 옛 exe를 되돌려 연다. 새 앱이 응답하기까지 걸린 시간을 작업 요약에 적는다. 이때 새 앱은 창 모드로 열린다.

준비(1)가 끝나면 2부터는 앞 단계가 실패해도 모두 돈다. 실패는 한 번에 모두 보이고, 하나라도 실패하면 작업은 실패다. 모델이 필요한 4와 6은 모델을 받았을 때만, 7과 8은 빌드가 성공했을 때만 돈다.

## 알려진 한계

- 4번은 CI 러너에 설치된 언어만 본다. 나머지 언어의 시험은 그 언어 도구가 있는 기기에서 돌려야 한다.
- `windows` 작업은 처음 실행 경고(SmartScreen)를 보지 않는다. 창 모드(WebView2)는 8에서 열기만 하고, 확인은 서버의 응답으로 한다.
