# Go

컴파일과 실행은 `go build -o app .` 다음 `./app`이다. `go`가 없으면 건너뛴다.

## 함수 모드

`function/solution.go`의 `solution`을 호출한다. 샘플 인자는 `[]int`다.

호출 코드(`algoblock_main.go`)는 채점할 때 선언을 읽어 만든다(아래).

## 프로그램 모드

`program/main.go`의 `main`이 표준 입력으로 개수와 숫자를 읽고 합을 출력한다.

## 채점 코드(runner.py)

함수 모드는 같은 `package main`에 `algoblock_main.go`를 더해 `solution`을 부르고 `encoding/json`으로 출력한다. `a, b int`처럼 묶은 인자 형도 읽는다. 작업 폴더에 `go.mod`를 둔다.

진입점: `func solution`이 함수, `func main()`이 프로그램 진입점이다. 모드를 정할 때와 다른 모드로 다시 실행할지 정할 때 이것을 본다.
