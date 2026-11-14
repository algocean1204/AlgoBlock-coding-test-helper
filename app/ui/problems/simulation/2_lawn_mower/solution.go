package main

func solution(garden []string, commands string) int {
	rows, cols := len(garden), len(garden[0])
	// 위, 오른쪽, 아래, 왼쪽: 시계 방향 순서. 오른쪽으로 돌면 +1, 왼쪽으로 돌면 -1
	dr := []int{-1, 0, 1, 0}
	dc := []int{0, 1, 0, -1}
	row, col := 0, 0
	for r := 0; r < rows; r++ {
		for c := 0; c < cols; c++ {
			if garden[r][c] == 'S' {
				row, col = r, c
			}
		}
	}
	direction := 0
	mowed := make([][]bool, rows)
	for r := range mowed {
		mowed[r] = make([]bool, cols)
	}
	mowed[row][col] = true
	count := 1
	for _, command := range commands {
		if command == 'L' {
			direction = (direction + 3) % 4 // 왼쪽으로 한 번 = 오른쪽으로 세 번(음수의 나머지가 음수가 되는 것을 피한다)
		} else if command == 'R' {
			direction = (direction + 1) % 4
		} else {
			nextRow, nextCol := row+dr[direction], col+dc[direction]
			if nextRow >= 0 && nextRow < rows && nextCol >= 0 && nextCol < cols &&
				garden[nextRow][nextCol] != '#' {
				row, col = nextRow, nextCol
				if !mowed[row][col] {
					mowed[row][col] = true
					count++
				}
			}
		}
	}
	return count
}
