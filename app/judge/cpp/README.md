# C++

컴파일러는 `g++` 또는 `clang++`다. 기준은 `-std=c++17`이다.

## 함수 모드

`function/solution.cpp`의 `solution`을 호출한다. 샘플 인자는 `std::vector<int>`다.

호출 코드(`algoblock_main.cpp`)는 채점할 때 선언을 읽어 만든다(아래).

## 프로그램 모드

`program/main.cpp`의 `main`이 표준 입력으로 개수와 숫자를 읽고 합을 출력한다.

두 모드 모두 `app`으로 컴파일한 뒤 `./app`을 실행한다.

## 채점 코드(runner.py)

함수 모드는 제출 파일을 `#include`한 `algoblock_main.cpp`를 만든다. 인자는 `vector<vector<int>>`, `string` 같은 선언을 읽어 리터럴로 넣는다. `-std=c++17 -O2 -I.`로 컴파일하고, `bits/stdc++.h`는 작업 폴더의 같은 이름 헤더가 받는다. macOS 링커가 기본 SDK를 읽지 못하면 설치된 다른 SDK로 다시 링크한다.

진입점: `solution(`이 함수, `int main(`이 프로그램 진입점이다. 모드를 정할 때와 다른 모드로 다시 실행할지 정할 때 이것을 본다.
