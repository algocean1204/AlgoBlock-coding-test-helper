# Java

Java 17 기준이다. 컴파일은 `javac`, 실행은 `java`다.

## 함수 모드

`function/Solution.java`의 `solution`을 호출한다. 샘플은 `int[]`를 받아 합을 `int`로 반환한다.

호출 코드(`FunctionRunner.java`)는 채점할 때 선언을 읽어 만든다(아래).

## 프로그램 모드

`program/Main.java`의 클래스 이름은 `Main`이다. `main`이 표준 입력을 읽고 합을 출력한다.

컴파일에 실패하면 `compile_error`, 실행이 10초를 넘기면 `timeout`이다.

## 채점 코드(runner.py)

함수 모드는 `solution` 선언(`int[][] grid, String word` 같은)을 읽어 케이스마다 리터럴로 부르는 `FunctionRunner.java`를 만든다. 반환값은 배열·리스트·맵까지 JSON으로 출력한다. 컴파일은 `javac -encoding UTF-8`, 실행은 `java -Xss256m`(깊은 재귀)이다.

진입점: `class Solution`과 `solution(` 메서드가 함수, `class Main`과 `static void main`이 프로그램 진입점이다. 모드를 정할 때와 다른 모드로 다시 실행할지 정할 때 이것을 본다.
