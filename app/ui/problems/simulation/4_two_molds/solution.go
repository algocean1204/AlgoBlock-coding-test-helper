package main

// grid에서 (r, c)와 맞닿은 칸 가운데 mold인 칸의 수
func countAround(grid [][]byte, r, c int, mold byte) int {
	n, m := len(grid), len(grid[0])
	dr := []int{-1, 1, 0, 0}
	dc := []int{0, 0, -1, 1}
	total := 0
	for d := 0; d < 4; d++ {
		nr, nc := r+dr[d], c+dc[d]
		if nr >= 0 && nr < n && nc >= 0 && nc < m && grid[nr][nc] == mold {
			total++
		}
	}
	return total
}

func copyGrid(grid [][]byte) [][]byte {
	out := make([][]byte, len(grid))
	for r := range grid {
		out[r] = append([]byte{}, grid[r]...)
	}
	return out
}

func solution(dish []string, hours int) []string {
	n, m := len(dish), len(dish[0])
	board := make([][]byte, n)
	for r := range dish {
		board[r] = []byte(dish[r])
	}
	for hour := 0; hour < hours; hour++ {
		// 1단계(번식): 1시간이 시작될 때의 board를 보고, 결과는 grown에 적는다
		grown := copyGrid(board)
		for r := 0; r < n; r++ {
			for c := 0; c < m; c++ {
				if board[r][c] != '.' {
					continue
				}
				a, b := countAround(board, r, c, 'A'), countAround(board, r, c, 'B')
				if a > b {
					grown[r][c] = 'A'
				} else if b > a {
					grown[r][c] = 'B'
				} else if a > 0 {
					grown[r][c] = '#'
				}
			}
		}
		// 2단계(포위): 1단계가 끝난 grown을 보고, 결과는 result에 적는다
		result := copyGrid(grown)
		for r := 0; r < n; r++ {
			for c := 0; c < m; c++ {
				if grown[r][c] == 'A' && countAround(grown, r, c, 'B') >= 3 {
					result[r][c] = '#'
				} else if grown[r][c] == 'B' && countAround(grown, r, c, 'A') >= 3 {
					result[r][c] = '#'
				}
			}
		}
		same := true // 1시간 동안 아무것도 바뀌지 않았으면 그 뒤로도 계속 같다
		for r := 0; r < n; r++ {
			if string(result[r]) != string(board[r]) {
				same = false
			}
		}
		if same {
			break
		}
		board = result
	}
	answer := make([]string, n)
	for r := range board {
		answer[r] = string(board[r])
	}
	return answer
}
