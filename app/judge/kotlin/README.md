# Kotlin

컴파일은 `kotlinc`, 실행은 `java -jar`다. 이 기기에는 `kotlinc`가 없으면 `toolchain_missing`으로 건너뛴다.

## 함수 모드

`function/Solution.kt`의 `solution`을 호출한다. 샘플은 `IntArray`를 받아 `Int`를 반환한다.

호출 코드(`FunctionRunner.kt`)는 채점할 때 선언을 읽어 만든다(아래).

## 프로그램 모드

`program/Main.kt`의 `main`이 표준 입력을 읽고 합을 출력한다.

두 모드 모두 `app.jar`로 만든 뒤 `java -jar app.jar`로 실행한다.

## 채점 코드(runner.py)

함수 모드는 `fun solution` 선언(`Array<IntArray>`, `String` 같은)을 읽어 `FunctionRunner.kt`를 만든다. `class Solution`이 있으면 `Solution().solution(...)`, 없으면 최상위 `solution(...)`을 부른다. `kotlinc` 첫 실행은 10초를 넘을 수 있어 컴파일 제한은 60초다.

진입점: `fun solution`이 함수, `fun main`이 프로그램 진입점이다. 모드를 정할 때와 다른 모드로 다시 실행할지 정할 때 이것을 본다.
