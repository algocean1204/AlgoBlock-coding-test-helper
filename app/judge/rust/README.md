# Rust

컴파일은 `rustc`, 실행 파일 이름은 `app`이다.

## 함수 모드

`function/solution.rs`의 `solution`을 호출한다. 샘플 인자는 `Vec<i32>`다.

호출 코드(`algoblock_main.rs`)는 채점할 때 선언을 읽어 만든다(아래).

## 프로그램 모드

`program/main.rs`의 `main`이 표준 입력으로 개수와 숫자를 읽고 합을 출력한다.

## 채점 코드(runner.py)

함수 모드는 `algoblock_main.rs`가 `include!("solution.rs")`로 제출 코드를 같은 모듈에 넣고 부른다. `pub`이 없어도 된다. 인자는 `Vec<Vec<i32>>`, `String`, `&str`, `usize` 같은 선언을 읽어 리터럴로 넣는다. `rustc --edition 2021 -O`로 컴파일한다.

진입점: `fn solution`이 함수, `fn main()`이 프로그램 진입점이다. 모드를 정할 때와 다른 모드로 다시 실행할지 정할 때 이것을 본다.
