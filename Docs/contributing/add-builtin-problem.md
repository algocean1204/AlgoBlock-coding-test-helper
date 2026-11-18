# 기본 문제 추가하기

이 문서는 기본 문제 폴더에 무엇을 넣는지, 어떻게 검사하고 묶는지, `ready.json`에서 무엇을 손으로 고칠 수 있는지 답한다. 기본 문제는 주제 15개 × 단계 5개 = 75문제이며 문제 하나가 폴더 하나다. 본보기는 `app/ui/problems/hash/1_popular_shelf/`다. 새 문제를 쓰기 전에 이 폴더의 파일을 모두 읽는다.

```
app/ui/problems/<주제>/<단계>_<이름>/
```

## 쓰기 전에

새 문제는 주제 폴더 아래 `<단계>_<이름>` 폴더로 둔다. 단계는 1~5 가운데 하나다. 다른 언어로도 풀게 하려면 `solution.java`처럼 언어마다 정답 풀이 파일을 넣는다. 없으면 그 문제는 Python으로만 풀 수 있다(묶인 `languages`가 `python`뿐이고, 서버는 다른 언어로의 전환을 거절한다).

주제와 단계의 뜻, 폴더에 넣는 파일, `problem.json`의 칸, 문제 글 규칙, `gen.py`가 만들 함수는 [app/ui/problems/README.md](../../app/ui/problems/README.md)에 있다. 다른 곳의 문제 글·문장·숫자·예시는 옮기지 않는다. 유형만 참고하고 새로 쓴다.

## 검사하기

`app`에서 돌린다. 모델을 부르지 않는다.
```bash
cd app
python3 ui/problemkit.py check ui/problems/<주제>                  # 주제 폴더 전체
python3 ui/problemkit.py check ui/problems/<주제>/<단계>_<이름>      # 문제 하나
python3 ui/problemkit.py check ui/problems/<주제> --langs           # 다른 언어 정답 풀이까지
```

검사는 다음을 본다.

1. `problem.json`의 필수 키·형·실전 신호, 그리고 케이스(예시 3개, 정확성, 효율성)의 형·크기·중복.
2. `solution.py`로 기대 결과를 정한다. 예시·정확성 케이스는 10초의 1/3, 효율성 케이스는 정한 Python 제한의 1/3 안에 끝나야 한다.
3. `brute.py`와 예시·정확성 케이스를 대조하고, 무작위 입력 300개로 대조한다. 결과 종류가 3가지(bool은 2가지) 이상이어야 한다.
4. `wrong_*.py`가 케이스 하나 이상에서 걸리는지. `slow_*.py`가 Python 제한에서 효율성 케이스를 시간 초과하고 정확성 케이스는 맞히는지.
5. `--langs`를 붙이면 다른 언어 정답 풀이가 모든 케이스를 통과하고, 그 언어 제한의 절반 안에 끝나는지.
6. 언어 함정 풀이(`lang_<번호>.<확장자>`)의 첫 줄 id가 함정 목록에 있는지, 정답 풀이에서 실수 하나만 바꿨는지, 케이스 하나 이상에서 실제로 떨어지는지. Python은 늘 돌리고 다른 언어는 `--langs`일 때 돌린다. 끝에 함정 목록(`app/ui/problems/lang_traps.json`)의 모양과, 어느 문제에서도 쓰지 않는 항목이 없는지를 본다.

공개 예시(`problem.json`의 `examples`)는 케이스에 자동으로 들어간다. 생성기(`gen.small`)에 같은 예시를 다시 적으면 '같은 케이스가 두 번 들어 있다'로 검사에 걸리고, 어느 케이스인지 알려 준다.

통과하면 `통과 <폴더>`가 나오고 `cases.json`(효율성 케이스가 있으면 `limits.json`, 언어 함정 풀이가 있으면 `lang.json`)이 생긴다. 실패하면 `실패`와 이유 목록이 나오고 종료 코드는 1이다.

## 언어 함정 더하기

해설의 정답 코드 위에는 고른 언어로 풀 때 조심할 것이 보인다. 이 글은 채점기로 그 문제에서 실제로 틀리는 것이 확인된 것만 보인다.

1. `app/ui/problems/lang_traps.json`의 그 언어 목록에서 이 문제에 맞는 함정을 고른다. 글은 이 목록에만 있다. 맞는 것이 없으면 항목을 더한다(언어마다 12개까지, 그 언어의 일반 사실만).
2. 문제 폴더에 `lang_<번호>.<확장자>`를 만든다. 같은 언어의 정답 풀이를 복사해 그 실수 하나만 넣고, 첫 줄에 `// 언어 함정: <id>`(Python은 `#`)를 적는다. 문제 글의 구절을 함께 보이려면 `// 언어 함정: <id> @ "구절"`처럼 적는다(둘까지. 무엇이 커지거나 깊어지는지 보이는 가장 짧은 말).
3. `python3 ui/problemkit.py try <문제 폴더> <파일>`로 떨어지는지 먼저 보고, `check <문제 폴더> --langs`로 검사해 `lang.json`을 쓴다.

칸의 뜻과 검사의 자세한 규칙은 [app/ui/problems/README.md](../../app/ui/problems/README.md)의 '언어 함정'에 있다.

효율성 케이스의 제한 시간을 정하는 식은 [채점기 문서](../architecture/judge.md)와 위 README의 '제한 시간'에 있다.

## 묶기

검사를 통과한 문제를 `app/ui/builtin.json`으로 묶는다. 묶는 스크립트는 패키지가 필요해서 `uv`로 돌린다(`python3`로 직접 돌리면 `langgraph`가 없어 실패한다).

```bash
cd app
uv run --no-project --python 3.12 --with langgraph --with pypdf python ui/make_builtin.py build --no-model                     # 모델을 부르지 않는다
uv run --no-project --python 3.12 --with langgraph --with pypdf python ui/make_builtin.py build --no-model --only hash/1_popular_shelf  # 문제 하나만 검사해 묶는다
uv run --no-project --python 3.12 --with langgraph --with pypdf python ui/make_builtin.py build                                # 낡은 가이드와 블록을 모델로 만든다
uv run --no-project --python 3.12 --with langgraph --with pypdf python ui/make_builtin.py build --model claude/claude-opus-5-5:high  # 만들 때 쓸 모델:추론 정도
```

- 기본은 다른 언어 정답 풀이(`solution.java` 등)도 검사해 싣는다. 그 언어의 도구가 기기에 있어야 한다. 이 기능을 끄는 `--no-langs`는 기존 문제의 다른 언어 풀이를 묶음에서 빼므로, 올릴 묶음에는 쓰지 않는다.
- `--only <주제>/<폴더>`: 그 문제만 검사하고 묶는다. 다른 문제의 행은 지금 `builtin.json`의 것을 그대로 둔다. 문제 하나를 더할 때 쓴다.
- `--no-model`: `ready.json`이 지금 글·정답 풀이와 맞으면 가이드와 블록을 싣는다. 모델 키 없이 만든 문제에는 `ready.json`이 없으므로 가이드·블록·힌트 없이 싣고 알림만 한다. `ready.json`의 출처 값이 지금과 다르면(이미 있던 가이드가 낡았으면) 그 문제와 까닭을 알리고 실패로 끝난다. 다른 언어의 줄 구간도 같다. 없거나 나눌 수 없다고 적힌 언어는 그 언어의 가이드·블록 없이 싣고 알림만 하고, 낡았으면 실패로 알린다.
- `--no-model`이 없으면 `ready.json`이 없거나 낡은 문제(글, 제한사항, `solution.py`가 바뀐 문제)의 가이드와 블록을 모델로 만든다. 다른 언어의 줄 구간(`ready.json`의 `langs`)이 없거나 낡았으면 그것도 받는다. 키가 있어야 한다. 세 번까지 만들어 보고(줄 구간은 앞 답과 그 답을 쓸 수 없었던 까닭을 붙여 다시 받는다), 안 되면 가이드 없이(줄 구간이면 그 언어만 빼고) 싣는다.
- `ALGOBLOCK_UI_CLIENT=cli`를 주면 모델 대신 이 PC의 Claude Code(`claude -p`)를 부른다. 개발용이며 키를 쓰지 않는다.
- `--redo <ID> …`는 그 문제들의 가이드와 블록, 다른 언어의 줄 구간을 다시 만든다.
- `--no-check`는 검사를 다시 돌리지 않고 `cases.json`과 `lang.json`을 믿는다. 개발과 시험용이며 실을 때는 쓰지 않는다.
- 언어 함정은 묶음에 실리는 언어의 것만 `lang.json`에서 싣는다(`--no-langs`면 Python 것만).
- 검사, 가이드 만들기, `ready.json` 모양 검사 가운데 하나라도 실패한 문제가 있으면 종료 코드는 1이다.

## ready.json

`ready.json`은 `source`와 `ready`로 이루어진다. `source`는 문제 글, 제한사항, `solution.py`에서 계산한 값이다. 이 값이 지금과 다르면 `--no-model` 빌드는 실패로 끝나고(가이드와 상관없는 수정이면 `app/ui/problems/README.md`대로 출처 값을 맞춘다), 모델을 부르는 빌드는 이 파일을 새로 써서 손으로 고친 것이 사라진다. `--redo`로 고른 문제도 새로 쓴다.

| 손으로 고쳐도 되는 것 | 고치면 안 되는 것 |
| --- | --- |
| 블록의 `name`, `goal`, `checks`, `hints` | 블록의 `reference`, `lines` |
| `solution`의 `approach`, `steps`, `clues` | `solution`의 `code`(`solution.py`와 한 글자도 달라지면 안 된다) |

빌드는 싣기 전에 모양을 본다.

- 블록 `reference`를 줄바꿈으로 이은 것이 `solution.code`와 같고, `solution.code`는 `solution.py`와 같아야 한다(끝 줄바꿈 제외). 블록에 `lines`가 있으면 1부터 빈틈과 겹침 없이 `reference`의 줄을 덮어야 한다.
- 블록마다 `hints`가 3개 이상이고 빈 것이 없으며, `name`과 `goal`이 비어 있지 않아야 한다. `solution.clues`는 비어 있지 않고 `solution.verified`는 참이어야 한다.

모양 검사에 걸린 문제는 실패로 나오고 가이드 없이 실린다.

`langs`는 다른 언어의 가이드와 블록을 만드는 줄 구간이다. 언어마다 `source`(Python 블록의 `reference`와 그 언어 정답 풀이에서 계산한 값), `lines`(블록마다 그 언어 정답 풀이에서 맡은 `[처음, 끝]` 줄), 그리고 있을 때만 `hints`가 있다. 블록의 이름, 목표, 확인, 힌트와 단서, 방향, 단계는 Python 것을 그대로 쓴다. Python 힌트가 그 언어 정답 풀이에 없는 코드 이름(다른 언어 풀이에만 있고 문제 글에도 없는 이름)을 부를 때만 그 자리에 `hints`의 힌트를 쓴다. 블록 id마다 Python 힌트와 같은 길이의 목록이고, Python 힌트를 그대로 쓰는 자리는 빈 글이다.

그 언어 정답 풀이를 Python 블록과 같은 차례·같은 일의 이어진 줄로 나눌 수 없으면 `lines` 대신 `"fits": false`가 적힌다. Python 블록의 단계가 그 언어 풀이에는 없거나 다른 블록과 합쳐졌을 때(예: 방향 표 없이 반복 안에서 바로 따짐, 비교 기준을 정렬 안에 바로 씀, 정렬 대신 최댓값과 합을 씀), 도움 함수가 Python 풀이와 다른 자리에 있을 때, 같은 일을 다른 방법(예: 묶음을 만들어 정렬하는 대신 비교 함수로 정렬)으로 짰을 때다. 이 언어는 싣지 않고 알림만 한다. 그 언어로 처음 튜터를 시작할 때 만든다. `source`가 바뀌거나 `--redo`로 고르면 다시 묻는다. 이 칸들은 손으로 고치지 않는다.

빌드는 다른 언어마다 싣기 전에 이것을 본다.

- `source`가 지금과 같고, `lines`가 블록마다 하나씩 그 언어 정답 풀이를 1번 줄부터 끝 줄까지 빈틈과 겹침 없이 나눈다.
- 이어 붙인 가이드와 블록이 위의 모양 검사를 통과하고, 틀 줄·빈 줄·주석만 있는 블록이 없다.
- 블록마다 같은 자리의 Python 블록과 같은 일을 한다(`make_builtin.py`의 `misfits`). 모델 없이 이름과 줄을 견준다. 이런 블록이 걸린다: Python 블록에는 일을 하는 줄이 있는데 함수 머리·값 없는 선언·틀 줄만 있다. Python 블록이 쓰는 이름은 대부분 다른 블록에 있고 이 블록의 이름도 다른 Python 블록의 것이다. Python 블록과 거의 같은 줄들이 대부분 다른 블록에 있다. Python 블록이 만들어 뒤 블록에 넘기는 이름(방향 표, 비교 함수 등. 반복 변수와 `LIMIT = 24`처럼 글자 그대로의 값을 붙인 이름은 빼고)이 그 언어 풀이 어디에도 없고, 이 블록에 그 줄과 닮은 줄도 이름만 바꿔 새로 만든 것도 없다.
- 힌트가 그 언어 정답 풀이에 없는 코드 이름을 부르지 않고, 한 언어에만 있는 낱말을 쓰지 않는다.

걸린 언어는 실패로 나오고 그 언어의 가이드와 블록 없이 실린다. 그 언어로 처음 튜터를 시작할 때 만든다. 모델로 build하면 걸린 까닭과 그 구간을 붙여 줄 구간을 다시 받는다.

## 알려진 한계

- 형 검사기는 `double`을 받지만, 기본 문제에서는 쓰지 않는다.
