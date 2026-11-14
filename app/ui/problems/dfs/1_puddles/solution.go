package main

func solution(floor []string) int {
	rows, cols := len(floor), len(floor[0])
	visited := make([][]bool, rows)
	for r := range visited {
		visited[r] = make([]bool, cols)
	}
	dr := []int{-1, 1, 0, 0}
	dc := []int{0, 0, -1, 1}
	count := 0
	for r := 0; r < rows; r++ {
		for c := 0; c < cols; c++ {
			if floor[r][c] != '#' || visited[r][c] {
				continue
			}
			// 아직 어느 웅덩이에도 들지 않은 물 칸: 새 웅덩이를 하나 세고, 이어진 칸을 모두 방문 표시한다
			count++
			visited[r][c] = true
			stack := [][2]int{{r, c}}
			for len(stack) > 0 {
				now := stack[len(stack)-1]
				stack = stack[:len(stack)-1]
				for d := 0; d < 4; d++ {
					nextR, nextC := now[0]+dr[d], now[1]+dc[d]
					if nextR < 0 || nextR >= rows || nextC < 0 || nextC >= cols {
						continue // 바닥 밖
					}
					if floor[nextR][nextC] == '#' && !visited[nextR][nextC] {
						visited[nextR][nextC] = true
						stack = append(stack, [2]int{nextR, nextC})
					}
				}
			}
		}
	}
	return count
}
