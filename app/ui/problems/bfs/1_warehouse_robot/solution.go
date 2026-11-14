package main

func solution(floor []string) int {
	rows, cols := len(floor), len(floor[0])
	startR, startC := 0, 0
	for r := 0; r < rows; r++ {
		for c := 0; c < cols; c++ {
			if floor[r][c] == 'S' {
				startR, startC = r, c
			}
		}
	}
	// distance[r][c]: 출발 칸에서 (r, c)까지의 이동 횟수. -1은 아직 가 보지 않은 칸
	distance := make([][]int, rows)
	for r := range distance {
		distance[r] = make([]int, cols)
		for c := range distance[r] {
			distance[r][c] = -1
		}
	}
	distance[startR][startC] = 0
	// Go에는 큐가 없어서 슬라이스와 읽는 위치(head)로 만든다
	queue := [][2]int{{startR, startC}}
	dr := []int{-1, 1, 0, 0}
	dc := []int{0, 0, -1, 1}
	for head := 0; head < len(queue); head++ {
		r, c := queue[head][0], queue[head][1]
		if floor[r][c] == 'E' {
			return distance[r][c]
		}
		for d := 0; d < 4; d++ {
			nr, nc := r+dr[d], c+dc[d]
			if nr < 0 || nr >= rows || nc < 0 || nc >= cols {
				continue
			}
			if floor[nr][nc] == '#' || distance[nr][nc] != -1 {
				continue
			}
			distance[nr][nc] = distance[r][c] + 1 // 넣을 때 바로 적어야 같은 칸이 두 번 들어가지 않는다
			queue = append(queue, [2]int{nr, nc})
		}
	}
	return -1
}
