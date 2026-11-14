package main

func solution(board []string) int64 {
	rows, cols := len(board), len(board[0])
	const (
		NEW     = 0 // 아직 안 감
		ON_PATH = 1 // 지금 걷는 길 위
		DONE    = 2 // 점수가 정해짐
	)
	state := make([][]int, rows)
	order := make([][]int, rows) // 지금 길에서 몇 번째로 밟은 칸인가
	score := make([][]int, rows)
	for r := 0; r < rows; r++ {
		state[r] = make([]int, cols)
		order[r] = make([]int, cols)
		score[r] = make([]int, cols)
	}
	for startR := 0; startR < rows; startR++ {
		for startC := 0; startC < cols; startC++ {
			if state[startR][startC] == DONE {
				continue
			}
			// 1. 밖으로 나가거나, 점수가 정해진 칸에 닿거나, 지금 길 위의 칸에 다시 닿을 때까지 걸으며 길을 적는다
			path := []int{} // 칸 번호 = 행 * cols + 열
			r, c := startR, startC
			nextScore := 0
			for {
				state[r][c] = ON_PATH
				order[r][c] = len(path)
				path = append(path, r*cols+c)
				switch board[r][c] {
				case 'U':
					r--
				case 'D':
					r++
				case 'L':
					c--
				default:
					c++
				}
				if r < 0 || r >= rows || c < 0 || c >= cols {
					nextScore = 0 // 밖이다: 더 밟을 칸이 없다
					break
				}
				if state[r][c] == DONE {
					nextScore = score[r][c] // 답을 아는 칸: 더 걷지 않고 이어 쓴다
					break
				}
				if state[r][c] == ON_PATH {
					// 고리: 다시 닿은 칸부터 지금 칸까지. 고리 위의 칸은 어디서 출발하든 고리를 한 바퀴 돈다
					first := order[r][c]
					length := len(path) - first
					for _, cell := range path[first:] {
						score[cell/cols][cell%cols] = length
						state[cell/cols][cell%cols] = DONE
					}
					path = path[:first] // 남은 것은 고리로 들어가기 전의 칸들
					nextScore = length
					break
				}
			}
			// 2. 걸어온 길을 거꾸로 돌아오며 '다음 칸의 점수 + 1'을 적는다
			for i := len(path) - 1; i >= 0; i-- {
				nextScore++
				score[path[i]/cols][path[i]%cols] = nextScore
				state[path[i]/cols][path[i]%cols] = DONE
			}
		}
	}
	var total int64 = 0 // 합은 최대 약 6백억이라 int64로 둔다
	for _, row := range score {
		for _, s := range row {
			total += int64(s)
		}
	}
	return total
}
