# JavaScript

실행 명령은 `node`다. 컴파일 단계는 없다.

## 함수 모드

`function/solution.js`의 `solution`을 호출한다. 샘플 입력 `[[1, 2, 3]]`은 `solution([1, 2, 3])`이다. 반환값은 JSON 한 줄로 출력한다.

## 프로그램 모드

`program/main.js`의 `main`을 실행한다. 표준 입력의 첫 줄은 개수, 다음 줄들은 숫자다. 합을 한 줄로 출력한다.

루트 `run.py`가 `runner.py`를 불러 `node <파일>`로 실행한다.

## 채점 코드(runner.py)

함수 모드는 `algoblock_runner.js`가 제출 글을 `vm`으로 돌린 뒤 `solution(...인자)`를 부른다. `module.exports`가 없어도 된다.

진입점: `function solution`·`const solution =`이 함수, `fs.readFileSync(0)`·`readline`·`process.stdin`·`function main`이 프로그램 진입점이다. 모드를 정할 때와 다른 모드로 다시 실행할지 정할 때 이것을 본다.
