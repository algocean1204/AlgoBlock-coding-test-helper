# judge — 채점기

채점이 앱 안에서 어떻게 쓰이는지는 [Docs/architecture/judge.md](../../Docs/architecture/judge.md)에 있다. 이 문서는 채점기 폴더 자체의 사용법과 규칙이다.

언어마다 폴더를 두고, 그 안에 함수 모드와 프로그램 모드 폴더를 둔다. 손으로 실행해 볼 수도 있고(`run.py`), 폴더를 통째로 다른 프로젝트 안에 붙여 넣어 서버가 `judge.py`를 불러 쓸 수도 있다.

채점기는 문제 설명과 제출 코드를 보고 모드를 정한다. 앱(`app/ui/server.py`)은 문제에 저장한 방식을 `mode`로 넘기므로 이 판정을 쓰지 않는다.

- `solution`을 완성하라는 문제는 함수 모드다. `solution`을 호출하고 반환값을 비교한다.
- 표준 입력과 표준 출력, '예제 입력 N' 꼴의 표준 입출력 형식, Java 클래스 `Main`은 프로그램 모드다. 완성한 프로그램을 실행하고 출력을 비교한다.
- 설명이 두 모드를 같이 가리키면 코드를 본다. `solution`만 있으면 함수 모드, `main`이나 클래스 `Main`만 있으면 프로그램 모드다.
- 그래도 정할 수 없으면 채점하지 않고 이유를 출력한다.
- 고른 모드에 필요한 함수나 클래스가 없을 때만 다른 모드로 한 번 다시 실행한다. 틀린 답, 실행 오류, 시간 초과는 그 모드의 결과로 남긴다.

## 연결

```text
judge/
├── README.md
├── run.py          명령줄
├── judge.py        모드 정하기, 다른 모드로 한 번, 빌드·실행·비교
├── common.py       실행, 시간, 출력·메모리 상한, 비교
├── typemodel.py    인자 형 읽기, 리터럴 만들기
├── test_check.py   자체 시험
└── <언어>/
    ├── runner.py   진입점 찾기, 호출 코드 만들기, 빌드·실행 명령
    ├── README.md
    ├── function/
    │   ├── solution.<확장자>
    │   └── cases.json
    └── program/
        ├── main.<확장자>
        └── cases.json
```

언어는 Python, Java, JavaScript, C++, Rust 다섯이다.

## 실행

`app/judge`에서 언어 하나의 예시를 실행한다.

```bash
python3 run.py python
python3 run.py java --mode program
python3 run.py javascript --mode function --case 1
```

제출 코드 하나를 채점할 때는 `--source`를 쓴다. 모드는 문제 설명(`--problem`)과 코드로 정한다.

```bash
python3 run.py java --source Solution.java --cases cases.json --problem 문제.md
```

`cases.json`은 케이스 목록이거나 `{"function": [...], "program": [...]}`다. 다른 모드로 다시 실행하려면 두 모드 케이스가 모두 있어야 한다.

케이스 하나는 `{"id", "input", "expected"[, "timeout"(초)]}`다. 함수 모드의 `input`은 인자 배열의 JSON 글이고, 프로그램 모드의 `input`은 표준 입력 글이다.

## 다른 모듈에서 부르기

패키지가 아니라 경로로 불러온다. 이 폴더의 모듈은 `algoblock_check_*` 이름으로 올라가므로 다른 패키지의 `common`과 섞이지 않는다. 폴더를 통째로 어디에 옮겨도 그대로 돈다.

```python
import importlib.util
spec = importlib.util.spec_from_file_location("algoblock_check_judge", "<경로>/judge/judge.py")
judge = importlib.util.module_from_spec(spec); spec.loader.exec_module(judge)
report = judge.judge("python", source, cases, problem="solution 함수를 완성하세요")
```

`report`는 `{language, mode, fallback_from, status, reason, cases: [{id, status, time_ms, stdout, stderr, expected, line?, near?}], compile?, compile_line?}`다.

- `line`: 실행 오류가 난 줄(알 수 있을 때).
- `near`: `timeout`이 있는 케이스(앱에서는 효율성 케이스)가 제한의 80% 이상 걸리고 통과했을 때 참.
- `compile_line`: 컴파일 오류가 난 줄(알 수 있을 때).

## 결과

| status | 뜻 |
| --- | --- |
| `passed` | 모든 케이스 통과 |
| `failed` | 출력이 기대값과 다름 |
| `runtime_error` | 0이 아닌 종료 코드 |
| `timeout` | 실행 제한 초과(기본 10초, 케이스의 `timeout`으로 바꾼다) 또는 컴파일 60초 초과 |
| `output_limit` | 표준 출력이나 표준 오류가 4,000,000바이트를 넘어 끝냈다 |
| `memory_limit` | 실행 중 메모리가 2,048MB를 넘어 끝냈다 |
| `skipped` | 연속 시간 초과 3번 뒤라 돌리지 않은 케이스. 전체 상태는 앞선 `timeout`이 된다 |
| `compile_error` | 컴파일 실패(`compile.stderr`) |
| `toolchain_missing` | 컴파일러나 실행기가 없음. 그 언어는 건너뛴다 |
| `undecided` | 모드를 정할 수 없음. 채점하지 않고 이유를 낸다 |
| `entry_missing` | 고른 모드의 함수·클래스가 없고 다른 모드로도 돌 수 없음 |
| `unsupported_signature` | 함수 모드 호출 코드를 만들 수 없는 인자 형 |
| `bad_case` | 함수 모드 input이 인자 배열 JSON이 아님 |
| `no_cases` | 케이스가 없음 |

전체 status는 `passed`와 `skipped`가 아닌 첫 케이스의 status다. 건너뛴 케이스는 전체 상태를 정하지 않으므로, 건너뛰기 앞의 `timeout`이 전체 상태가 된다.

## 제한 시간

- 실행 한 번(케이스 하나)의 기본 제한은 10초다. 케이스에 `timeout`(초)을 주면 그 값을 쓴다. 컴파일 한 번은 60초다.
- `timeout`이 있는 케이스(앱에서는 효율성 케이스)는 제한의 1.3배에서 끝낸다. 제한을 넘었지만 1.3배 안에서 스스로 끝났으면 한 번 더 돌려 짧은 쪽으로 판정한다. 1.3배에서 끊긴 것은 다시 돌리지 않는다. 화면에 보이는 시간은 제한 시간이다.
- 연속 시간 초과가 세 번 이어지면 남은 케이스를 돌리지 않는다(`skipped`). 끝없는 반복 하나에 케이스 수 × 제한 시간을 기다리지 않게 하려는 것이다. 다른 결과가 나오면 연속 수는 0이 된다.
- 실행 중에는 출력이 4,000,000바이트(표준 출력과 표준 오류 각각)를 넘으면, 메모리가 2,048MB를 넘으면 자식 프로세스까지 끝낸다. 메모리는 0.25초마다 잰다(POSIX는 `ps rss`, Windows는 작업 집합). 컴파일러는 메모리를 보지 않는다.
- JSON으로 4,000자를 넘는 인자는 호출 코드에 리터럴로 박지 않고 파일로 넘긴다.

## 비교

- 함수 모드: 출력 마지막 줄을 JSON으로 읽어 기대값과 비교한다. JSON이 아니면 글로 비교한다.
  - 기대값이 정수면 정확히 같아야 한다. 실수로 낸 답(3.0)은 정확히 그 정수이고 절댓값이 2^53 이하일 때만 맞다.
  - 기대값이 실수면 상대 1e-6, 절대 1e-6 오차를 허용한다(`math.isclose`).
  - 불리언은 불리언끼리만 같다. 수와 섞지 않는다.
  - 목록은 길이와 원소, 객체는 키와 값을 비교한다.
  - 기대값이 따옴표 없는 글(`abc`)이면 반환된 문자열과 글로 비교한다.
- 프로그램 모드: 줄마다 끝 공백을 빼고, 끝의 빈 줄을 뺀 뒤 비교한다(`\r\n`도 같다). 앞 공백은 답의 일부다. 기본은 글자 그대로다. `judge(…, decimal=True)`(문제가 실수 답을 허용할 때)면 기대 출력에 소수로 적힌 낱말을 상대·절대 1e-6 오차 안에서 같게 본다.

## 함수 모드 호출 코드

`solution` 선언의 인자 형을 읽어 케이스마다 그 언어 리터럴로 부르는 코드를 만든다(`typemodel.py`). 받는 형은 정수, 긴 정수, 실수, 참/거짓, 문자열과 그 1·2차원 배열이다. 반환값은 언어마다 JSON으로 출력한다. 빌드는 한 번, 실행은 케이스마다 한 번이다.

## 제한과 한계

- macOS에서 기본 SDK와 링커가 맞지 않으면(`tapi error`) C++은 설치된 다른 SDK로 다시 링크한다.
- clang에는 `bits/stdc++.h`가 없어 C++ 작업 폴더에 같은 이름의 헤더를 둔다.
- 자식 프로세스에는 이름에 KEY, TOKEN, SECRET, PASSWORD, CREDENTIAL이 들었거나 `ALGOBLOCK_`, `ANTHROPIC_`, `OPENAI_`, `XAI_`, `OPENROUTER_`, `AWS_`, `GOOGLE_`, `AZURE_`, `GITHUB_`, `GH_`로 시작하는 환경 변수를 넘기지 않는다. `PYTHONUTF8=1`과 `PYTHONIOENCODING=utf-8`은 더한다.
- 제출 코드를 격리하지 않는다. 파일과 네트워크 접근은 막지 않는다. 격리가 필요하면 컨테이너나 OS 샌드박스가 필요하다.
- CPU 시간 상한: 제출 코드를 돌리는 프로세스마다 `ceil(제한 시간 × 4) + 5`초의 CPU 시간 상한을 건다. 부모 프로세스가 먼저 죽어도 끝없는 반복은 스스로 끝난다. POSIX는 `RLIMIT_CPU`, Windows는 작업 객체의 사용자 모드 시간 상한이다.
- 채점 중에 앱이 끝나면 돌던 채점을 정리한다(종료 신호, Ctrl+C, 창 닫기). 메뉴의 '끝내기'는 정리 코드가 돌지 않을 수 있다. 그때 POSIX는 CPU 시간 상한만 남고, Windows는 작업 핸들이 닫혀 모두 끝난다.
- POSIX: 새 세션으로 띄우고 끝나면 프로세스 그룹을 `SIGKILL`로 끝낸다. `setsid`로 새 세션을 만든 자식은 그룹 밖이라 잡지 못한다.
- Windows: 멈춘 채로 만들어 작업 객체(`KILL_ON_JOB_CLOSE`, 프로세스별 CPU 시간, 작업 전체 커밋 메모리 4,096MB, 동시 프로세스 64개, 처리되지 않은 예외는 바로 끝냄)에 넣은 뒤 재개한다. 프로세스 수 상한에 걸려 끝나면(알림을 받았을 때) 표준 오류에 한 줄이 붙는다. 프로세스를 만드는 동안 앱의 오류 모드(`SetErrorMode`)에 오류 창 끄기를 더해 자식이 물려받게 하고(DLL을 못 찾아도 창이 뜨지 않는다) 끝나면 되돌린다. 컴파일러에는 프로세스 수 상한을 걸지 않는다. 커밋 상한에 걸려 실행 오류로 끝나면 작업의 알림(완료 포트)을 보고 `memory_limit`로 판정한다. 실행 시간은 재개한 뒤부터 잰다. 끝나면 작업을 끝내 자식까지 모두 끝낸다. 콘솔 창은 띄우지 않는다(`CREATE_NO_WINDOW`). 실행 파일은 절대 경로로 바꿔 부른다(`./app` → 작업 폴더의 `app.exe` 또는 `app`, 그 밖은 PATH에서 찾은 경로).
- Windows에서 작업 객체를 쓰지 못하면 작업 없이 돌리고 결과에 `warning`(까닭)을 붙인다. 앱 서버는 이것을 화면의 한 줄(`notice`)로 옮긴다. 이때는 시간 초과와 상한 초과 때만 `taskkill /F /T`로 끝내고, 정상 종료한 주 프로세스의 자식은 남을 수 있다.

## 시험

```bash
cd app/judge
python3 -m unittest test_check
```

컴파일러가 없는 언어는 건너뛴다. POSIX 전용 시험(프로세스 그룹)은 Windows에서, Windows 전용 시험(작업 객체: 정상 종료 뒤의 자식, 커밋 메모리 상한, 프로세스 수 상한, 오류 창 끄기, 작업 없이 돌 때의 `warning`)은 다른 OS에서 건너뛴다.

시험이 보는 것: 모드 정하기, 비교, 5개 언어 두 모드(여러 케이스, 2차원 배열, 한글·따옴표 문자열), 형 있는 반환(긴 정수, 참/거짓, 실수 2차원), C++ 참조 인자, 큰 인자의 파일 전달, BigInt, 틀린 답, 실행 오류와 오류 줄 번호, 시간 초과, 연속 시간 초과 뒤 `skipped`, 제한 근처(`near`)와 다시 재기, 출력과 메모리 상한, 자식 프로세스 정리, CPU 시간 상한, Windows 작업 객체(구조체 배치, 실행 파일 경로), 비밀 환경 변수 거르기, 컴파일 오류, 다른 모드로 한 번 다시 실행, 정할 수 없음, 지원하지 않는 선언, 샘플 전체.
