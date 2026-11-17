# 데이터 폴더

AlgoBlock의 기록과 설정은 데이터 폴더 하나에 있다. 이 문서는 폴더 위치, 파일과 SQLite 표, 스키마 버전 처리, 기기 밖으로 나가는 것을 설명한다.

## 위치

| 실행 방식 | 기본 위치 |
|---|---|
| 소스 실행 | `app/ui/data`. 환경 변수 `ALGOBLOCK_UI_DATA`로 바꾼다. 없으면 만든다 |
| macOS 설치 파일 | `~/Library/Application Support/AlgoBlock` |
| Windows 설치 파일 | `%APPDATA%\AlgoBlock`. 없으면 `~/AppData/Roaming/AlgoBlock` |
| 그 밖의 설치 파일 | `$XDG_DATA_HOME/AlgoBlock`. 없으면 `~/.local/share/AlgoBlock` |

- 설치 파일도 `ALGOBLOCK_UI_DATA`가 이미 있으면 그 값을 쓴다.
- 소스 실행의 데이터 폴더는 `app/ui/data/.gitignore`에 따라 git에서 빠진다.
- 브라우저 쪽에는 문제마다 고른 푸는 방식이 로컬 저장소의 `algoblock.way.<문제 id>` 키로 남는다.

## 파일

| 파일 | 내용 |
|---|---|
| `tutor.db` | 튜터 엔진의 SQLite 파일 |
| `problems.json` | 등록 문제: 제목, 글, 케이스, 방식, 주제, 단계, 인자 이름, 대조 결과 `check`, 만든 케이스 `made`, 제한 `limits` |
| `blocks.json` | 블록 칸의 코드 |
| `codes.json` | 문제마다 언어별로 쓰던 코드 |
| `checkpoints.json` | 언어마다 마지막 체크포인트 |
| `attendance.json` | 출석한 날짜(기기의 현지 날짜) |
| `touched.json` | 문제를 마지막으로 손댄 시각(코드 저장, 실행, 제출, 힌트) |
| `hints.json` | 혼자 풀기에서 이번 풀이에 블록마다 본 힌트 수. 없거나 맞지 않으면 본 힌트 수를 블록 1부터 차례로 나눈다 |
| `keys.json` | 화면에서 넣은 API 키. 권한 0600 |
| `prefs.json` | 안내를 봤는지(`tour_seen`), 과정별 급과 추론 정도(`stages`), 마지막 풀이 언어(`language`), 화면 색(`scheme`: `light` 또는 `dark`. 없으면 운영체제 설정을 따른다), 세 칸의 너비 몫(`panes`) |
| `models.json` | 공급자 시리즈마다 최신 모델 이름과 받은 시각 |
| `kept.json` | 언어를 바꿀 때 보관한 그 언어의 가이드, 계획, 해설 |
| `.env` | 키(선택). 루트 `.env` 다음에 읽는다 |
| `auth/` | ChatGPT 로그인: 기기 아이디 `chatgpt-host.json`, 계정과 토큰 `chatgpt.json`(0600) |
| `usage.jsonl` | 모델 호출마다 한 줄. 토큰 수만 적는다 |
| `assets/<문제 id>/` | 등록할 때 올린 원본(`NN.<확장자>`)과 원래 이름을 적은 `index.json` |
| `large/<문제 id>/<번호>.json` | 효율성 케이스의 큰 입력과 기대 결과 |
| `vectors/` | 비슷한 문제 찾기 색인(로컬 Qdrant)과 임베딩 이름표 `embedder.txt` |
| `models/` | 임베딩 모델 폴더 |
| `updates/` | 업데이트: 받은 설치 파일(`<버전>/`), 업데이트 설정 `settings.json`(자동 확인 `auto`, 건너뛴 버전 `skip`, 마지막 확인 시각 `checked`, 그때 찾은 새 버전의 릴리스 요약 `release`), 바꿔 끼우기 스크립트(macOS `swap.sh`, Windows `swap.ps1`)와 기록 `swap.log`(다음에 켤 때 한 번 읽고 `swap.prev.log`로 옮긴다. Windows는 바꾸는 PowerShell 자체의 출력 `swap-out.log`(새 앱의 출력은 담지 않는다), 스크립트가 도는 동안의 표시 `swap.waiting`도). 지금 버전 이하의 받은 파일은 다음 실행 때 지운다 |
| `<이름>.broken-<때>` | 읽지 못한 JSON을 옮겨 둔 파일 |

- JSON 파일은 임시 파일에 쓴 뒤 바꿔 끼운다.
- 읽지 못한 JSON은 덮어쓰지 않고 `.broken-<때>`로 옮긴다. 서버는 기본값으로 시작한다.

## SQLite (`tutor.db`)

표는 12개다.

| 표 | 담는 것 |
|---|---|
| `setting` | 키와 값(`key`, `value`) 쌍. 다른 표와 달리 문제별로 나뉘지 않는다 |
| `problem` | 문제 기본 행 |
| `tutor_session` | 튜터 세션 상태(`solution_json` 포함) |
| `message` | 대화 말(사용자와 튜터)과 질문 유형(`move`) |
| `feedback` | 제출에 대한 피드백 |
| `submission` | 제출 코드, 통과 여부, 시각, 언어, 결과 종류, 상세(`detail_json`: 정확성·효율성 점수와 가장 긴 실행 시간) |
| `block_state` | 블록 판정('Y', 'N', '?'), 이름 짝(`renames_json`) |
| `debug_state` | 디버그 진단 상태 |
| `problem_fact` | 문제 뼈대: 기술(`skills_json`), 크기, 단계(`level`), 태그(`tags_json`) |
| `pitfall_hit` | 제출이 밟은 함정. 같은 코드 해시는 한 번만 센다 |
| `solution` | 풀이 가이드 |
| `study` | 학습 기록: 본 힌트 수, 해설을 처음 연 시각, 통과 전에 열었는지, 도움(튜터 기능·힌트·해설)을 처음 쓴 시각, 마지막 '처음부터' 시각과 그 뒤에 도움을 처음 쓴 시각, 그때까지 본 힌트 수 |

- 외래 키를 켠다. 문제를 지우면 그 문제의 행이 `ON DELETE CASCADE`로 같이 지워진다.
- `setting`을 뺀 모든 표는 `problem_id`로 나뉜다.

## 스키마 버전

- 버전은 `PRAGMA user_version`에 저장한다. 마이그레이션 목록(`MIGRATIONS`)의 길이가 최신 버전이다. 현재 버전은 10이다.
- DB를 열면 저장된 버전 다음부터 차례로 마이그레이션을 돈다. 남은 마이그레이션은 모두 한 트랜잭션 안에서 돈다. 쓰기 잠금(`BEGIN IMMEDIATE`)을 먼저 잡고, 실패하면 모두 되돌린다.
- 버전별 변경:
  - 2: `message`에 `move` 열
  - 3: `debug_state`, `problem_fact`, `pitfall_hit` 표
  - 4: `problem_fact`에 `skills_json`과 크기
  - 5: `solution` 표와 `tutor_session.solution_json`
  - 6: `submission`에 언어, 결과 종류, `detail_json`과 `study` 표
  - 7: `block_state.renames_json`
  - 8: 블록 판정에 '?' 추가(표를 새로 만들어 옮김)
  - 9: `problem_fact`에 `level`과 `tags_json`
  - 10: `study`에 `help_first_at`, `help_after_reset_at`, `reset_at`, `hints_at_reset`. 옛 행은 남은 기록으로 채운다(대화가 있던 문항은 행을 만든다. 본 힌트는 시각이 없어 가장 이른 시각으로 둔다)

## 기기 밖으로 나가는 것

| 나가는 곳 | 무엇이 나가는가 |
|---|---|
| `api.anthropic.com` (Claude API 키) | 튜터를 쓸 때의 문제 글, 내 말, 내 코드, 채점 결과. 문제를 넣을 때 올린 그림 장 |
| `api.openai.com` (OpenAI API 키, ChatGPT 로그인의 추론과 모델 목록) | 같음 |
| `auth.openai.com` (ChatGPT 로그인의 로그인, 토큰, 공개키) | 로그인 요청과 토큰 교환. 문제 글과 코드는 나가지 않는다 |
| `api.github.com`, `github.com` (업데이트 확인과 받기) | 확인: 요청 머리(`User-Agent: AlgoBlock/<버전>`, `Accept`)만. 받기: 릴리스 파일 주소로 내려받는다. 키, 문제, 기록은 나가지 않는다. 자동 확인을 끄면 확인하지 않는다 |

- 효율성 케이스의 큰 입력은 모델에 보내지 않는다. `(아주 큰 입력)`으로 바꿔 보낸다.
- 키는 공급자 요청 머리로만 나간다.
- 키나 ChatGPT 로그인이 연결돼 있으면 공급자의 모델 목록을 하루에 한 번 받는다.
- 키나 로그인이 없으면 모델을 부르지 않는다.
- 개발용 연결 '이 PC의 Claude Code'(`ALGOBLOCK_UI_CLIENT=cli`로 띄웠을 때만 화면에 나온다)를 고르면 로컬 `claude -p`를 부른다.

나가지 않는 것은 다음과 같다.

- 데이터 폴더와 DB 자체. 모두 기기 안에 있다.
- 채점. 제출 코드는 기기 안에서 돈다.
- 비슷한 문제 색인과 임베딩. 기기 안 모델로 돌고 키와 네트워크를 쓰지 않는다.
- 학습 보고서, 힌트, 기본 문제 해설, 표의 케이스 채우기. 모델을 쓰지 않는다.
- 사용량 기록(`usage.jsonl`). 키와 프롬프트 글을 적지 않는다.

임베딩 모델은 `app/tutor/knowledge/embed.py fetch`를 직접 실행할 때만 `huggingface.co`에서 받는다. 앱이 도는 중에는 받지 않는다. 파일이 없으면 벡터 검색을 끈다.

## 지우기

- 데이터 폴더를 지우면 등록 문제, 키, 기록이 모두 사라진다. 모두 이 폴더 안에 있기 때문이다.
- 화면의 '문제 삭제'는 등록 문제 하나와 그 문제의 기록을 지운다.

## 알려진 한계

- Windows에는 권한 비트가 없어 `keys.json`과 토큰 파일의 0600 설정이 적용되지 않는다.
