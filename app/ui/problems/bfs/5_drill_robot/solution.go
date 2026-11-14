package main

func solution(mine [][]int, drill int) int {
	rows, cols := len(mine), len(mine[0])
	dr := []int{-1, 1, 0, 0}
	dc := []int{0, 0, -1, 1}

	// 상태 = (행, 열, 지금까지 쓴 드릴 수). 같은 칸이라도 쓴 드릴 수가 다르면 다른 상태다
	// distance[r][c][used]: 그 상태까지의 최소 이동 횟수. -1은 아직 가 보지 않은 상태
	distance := make([][][]int, rows)
	for r := range distance {
		distance[r] = make([][]int, cols)
		for c := range distance[r] {
			distance[r][c] = make([]int, drill+1)
			for u := range distance[r][c] {
				distance[r][c][u] = -1
			}
		}
	}
	distance[0][0][0] = 0
	queue := [][3]int{{0, 0, 0}} // Go에는 큐가 없어서 슬라이스와 읽는 위치(head)로 만든다
	for head := 0; head < len(queue); head++ {
		r, c, used := queue[head][0], queue[head][1], queue[head][2]
		if r == rows-1 && c == cols-1 {
			return distance[r][c][used]
		}
		for d := 0; d < 4; d++ {
			nr, nc := r+dr[d], c+dc[d]
			if nr < 0 || nr >= rows || nc < 0 || nc >= cols {
				continue
			}
			nextUsed := used + mine[nr][nc] // 바위 칸이면 드릴을 한 번 더 쓴다
			if nextUsed > drill {
				continue
			}
			if distance[nr][nc][nextUsed] != -1 {
				continue
			}
			distance[nr][nc][nextUsed] = distance[r][c][used] + 1
			queue = append(queue, [3]int{nr, nc, nextUsed})
		}
	}
	return -1
}
