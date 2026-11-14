# Python

Python 3.9 기준이다. 실행 명령은 `python3`다. 컴파일 단계는 없다.

## 함수 모드

`function/solution.py`의 `solution`을 호출한다. 샘플은 숫자 배열의 합이다.

`cases.json`의 `input`은 JSON 배열이다. `[[1, 2, 3]]`은 `solution([1, 2, 3])`으로 들어간다. 반환값은 JSON으로 출력하고 기대값과 JSON으로 비교한다.

## 프로그램 모드

`program/main.py`를 그대로 실행한다. 샘플은 첫 줄의 개수만큼 숫자를 읽어 합을 출력한다.

`cases.json`의 `input`은 표준 입력 문자열이다. 표준 출력과 `expected`를 줄마다 끝 공백과 끝의 빈 줄을 빼고 비교한다.

루트 `run.py`가 이 폴더의 `runner.py`를 불러 두 모드를 실행한다.

## 채점 코드(runner.py)

함수 모드는 `algoblock_runner.py`가 제출 파일을 모듈로 불러 `solution(*인자)`(맨 위 함수가 없으면 `Solution().solution`)를 부르고 반환값을 JSON으로 출력한다. 제출 파일의 `if __name__ == "__main__"` 블록은 돌지 않는다.

진입점: `def solution`이 있으면 함수 모드 진입점, `input(`·`sys.stdin`·`def main`·`__main__` 블록이 있으면 프로그램 모드 진입점이다. 모드를 정할 때와 다른 모드로 다시 실행할지 정할 때 이것을 본다.
