# 채점 언어 추가하기

이 문서는 채점 언어를 하나 더할 때 고쳐야 하는 곳과 돌려 볼 시험을 답한다. 지금 채점하는 언어는 Python, Java, C++, JavaScript, Rust 다섯 개다. 채점기의 동작은 [judge.md](../architecture/judge.md)가 설명한다. 이 문서는 "어디를 고치나"만 다룬다. 아래 `<언어>`는 새 언어의 폴더 이름이고, `<확장자>`는 그 언어의 파일 확장자다.

## 고칠 곳

1. `app/judge/<언어>/runner.py`를 새로 만든다. 다음을 정의한다: `TOOLS`(또는 `toolchain()`, 필요한 도구 이름), `SAMPLE`, `ENTRY`, `defines_solution`, `defines_main`, `has_entry`, `prepare`, `command`. `prepare`가 빌드 명령을 돌려주면 `common.compile_command`로 컴파일한다. 컴파일을 따로 다뤄야 하면 `compile`을 정의한다(C++가 그렇다). 컴파일하는 언어는 `app/judge/rust/runner.py`를, 해석하는 언어는 `app/judge/python/runner.py`를 본보기로 본다.
2. `app/judge/judge.py`의 `LANGUAGES` 목록에 언어 이름을 더한다.
3. `app/judge/typemodel.py`에 형 이름을 읽는 `<언어>_type`과 리터럴을 쓰는 함수를 더한다. 함수 모드에서 `solution`의 인자 형을 읽어 호출 코드를 만드는 언어(Java, C++, Rust)가 여기에 해당한다.
4. `app/judge/common.py`의 오류 줄 찾기 규칙 `LINE_PATTERNS`에 필요하면 규칙을 더한다. 기본 규칙은 `<파일>:<줄>`이다. `HEAD_LINES`도 함께 본다.
5. 샘플 폴더를 만든다. 함수 모드는 `app/judge/<언어>/function/`, 프로그램 모드는 `app/judge/<언어>/program/`이고, 각각 `SAMPLE`에 적은 파일(예: Rust는 `solution.rs`·`main.rs`, Java는 `Solution.java`·`Main.java`)과 `cases.json`을 둔다. `app/judge/run.py`가 이 샘플을 읽는다.
6. `app/judge/test_check.py`의 언어별 소스 표 `SOURCES`와 큰 입력 표 `BIG_SOURCES`에 새 언어를 더한다.
7. `app/ui/stubs.py`의 `LANGUAGES`, 형 이름 표 `NAMES`, 표준 입출력 뼈대 `PROGRAM`에 더한다.
8. `app/ui/problemkit.py`의 확장자 표 `EXT`와 `load`가 읽는 확장자 목록에 더한다.
9. `app/ui/casegen.py`의 효율성 상한 `LIMIT`에 더한다. 없으면 `limit_of`가 KeyError를 낸다.
10. `app/ui/app.js`의 표시 이름 `LANG`, 도구 안내 `TOOL`, 언어 짐작 `LOOKS`, 중괄호를 쓰는 언어 목록 `BRACE_LANGS`에 더한다.
11. `app/ui/highlight.js`의 언어 표 `L`에 주석·문자열 규칙과 키워드를 더하고, `app/ui/test_highlight.js`의 `EXT`와 대표 토큰 `CASES`에 더한다.
12. 선택: `app/ui/server.py`의 실행 오류 풀이 표 `HINTS`와 `FAMILY`에 더한다.
13. 선택(macOS 앱): 새 도구가 Finder로 연 앱의 기본 PATH에 없는 곳에 깔린다면 `app/packaging/launcher.py`의 PATH 목록에 더한다.

서버의 언어 목록과 도구 확인은 `judge.LANGUAGES`를 그대로 쓰므로 `server.py`의 목록은 고치지 않는다.

## 시험

새 언어를 더한 뒤 아래를 돌린다.

```bash
cd app/judge && python3 -B -m unittest test_check      # 새 언어의 소스가 SOURCES와 BIG_SOURCES에 있어야 한다
cd app && uv run -q --no-project --python 3.12 --with langgraph --with pypdf python -B ui/test_server.py   # 화면 서버의 언어 목록과 도구 확인
cd app/judge && python3 run.py <언어>                   # 샘플 실행(함수 모드와 프로그램 모드)
cd app && python3 ui/problemkit.py stub ui/problems/hash/1_popular_shelf <언어>   # 시작 코드
```

- `test_check`는 기기에 없는 언어를 건너뛴다. 새 언어의 시험이 실제로 돌았는지 그 언어 도구가 있는 기기에서 확인한다.
- CI가 초록이어도 새 언어의 시험은 돌지 않았을 수 있다. 까닭은 [testing.md](testing.md#ci)를 본다.
- `app/ui/test_server.py`는 도구 목록과 문제의 언어 목록에서 언어 수를 7로 본다. 언어를 더하면 이 값도 고친다.
- `run.py`는 도구가 없어 `toolchain_missing`이 나와도 실패로 치지 않는다.
- 기본 문제에 새 언어의 정답 풀이(`solution.<확장자>`)를 넣었다면 `cd app && python3 ui/problemkit.py check ui/problems/<주제> --langs`로 검사한다. 정답 풀이를 넣는 일은 [add-builtin-problem.md](add-builtin-problem.md)를 본다.

## 알려진 한계

- 도구는 있는지만 확인한다. 버전은 확인하지 않는다.
- 빌드 옵션은 코드에 고정되어 있다. C++는 `-std=c++17`, Rust는 edition 2021로 빌드한다.
- 채점기는 파일이나 네트워크 접근을 막지 않는다. 새 언어의 실행기도 같은 방식으로 돈다. 환경 변수 거르기와 시간·출력·메모리 상한은 공통 코드가 맡는다.
