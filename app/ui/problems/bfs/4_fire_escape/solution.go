package main

func solution(building []string) int {
	rows, cols := len(building), len(building[0])
	dr := []int{-1, 1, 0, 0}
	dc := []int{0, 0, -1, 1}
	newGrid := func() [][]int {
		g := make([][]int, rows)
		for r := range g {
			g[r] = make([]int, cols)
			for c := range g[r] {
				g[r][c] = -1
			}
		}
		return g
	}

	// 1. 불: 불이 난 칸을 모두 처음부터 큐에 넣고 한 번에 퍼뜨린다(여러 출발점 BFS)
	// fire[r][c]: 불이 (r, c)에 닿는 시각. -1은 불이 끝내 닿지 않는 칸
	fire := newGrid()
	queue := [][2]int{} // Go에는 큐가 없어서 슬라이스와 읽는 위치(head)로 만든다
	startR, startC := 0, 0
	for r := 0; r < rows; r++ {
		for c := 0; c < cols; c++ {
			if building[r][c] == 'F' {
				fire[r][c] = 0
				queue = append(queue, [2]int{r, c})
			} else if building[r][c] == 'S' {
				startR, startC = r, c
			}
		}
	}
	for head := 0; head < len(queue); head++ {
		r, c := queue[head][0], queue[head][1]
		for d := 0; d < 4; d++ {
			nr, nc := r+dr[d], c+dc[d]
			if nr >= 0 && nr < rows && nc >= 0 && nc < cols && building[nr][nc] != '#' && fire[nr][nc] == -1 {
				fire[nr][nc] = fire[r][c] + 1
				queue = append(queue, [2]int{nr, nc})
			}
		}
	}

	// 2. 사람: 불보다 먼저 닿는 칸으로만 움직이는 BFS
	person := newGrid()
	person[startR][startC] = 0
	queue = [][2]int{{startR, startC}}
	for head := 0; head < len(queue); head++ {
		r, c := queue[head][0], queue[head][1]
		for d := 0; d < 4; d++ {
			nr, nc := r+dr[d], c+dc[d]
			if nr < 0 || nr >= rows || nc < 0 || nc >= cols {
				continue
			}
			if building[nr][nc] == '#' || person[nr][nc] != -1 {
				continue
			}
			arrive := person[r][c] + 1
			if fire[nr][nc] != -1 && fire[nr][nc] <= arrive { // 불이 같은 분이나 더 일찍 닿는 칸은 못 들어간다
				continue
			}
			if building[nr][nc] == 'E' {
				return arrive
			}
			person[nr][nc] = arrive
			queue = append(queue, [2]int{nr, nc})
		}
	}
	return -1
}
