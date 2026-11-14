package main

func solution(board [][]int, k int) [][]int {
	n, m := len(board), len(board[0])
	result := make([][]int, n)
	for r := range board {
		result[r] = append([]int{}, board[r]...)
	}
	limit := n
	if m < limit {
		limit = m
	}
	for ring := 0; ring < limit/2; ring++ {
		top, bottom, left, right := ring, n-1-ring, ring, m-1-ring
		// 고리의 칸을 왼쪽 위 모서리부터 시계 방향 순서로 늘어놓는다
		cells := [][2]int{}
		for c := left; c <= right; c++ {
			cells = append(cells, [2]int{top, c})
		}
		for r := top + 1; r <= bottom; r++ {
			cells = append(cells, [2]int{r, right})
		}
		for c := right - 1; c >= left; c-- {
			cells = append(cells, [2]int{bottom, c})
		}
		for r := bottom - 1; r > top; r-- {
			cells = append(cells, [2]int{r, left})
		}
		length := len(cells)
		shift := k % length // 칸 수만큼 돌면 제자리로 돌아온다
		if ring%2 == 1 {
			shift = (length - shift) % length // 반시계 방향으로 shift칸 = 시계 방향으로 length - shift칸(음수의 나머지를 피한다)
		}
		// 시계 방향으로 shift칸 돌면 i번째 칸의 보석은 i + shift번째 칸으로 간다
		for i := 0; i < length; i++ {
			to := cells[(i+shift)%length]
			result[to[0]][to[1]] = board[cells[i][0]][cells[i][1]]
		}
	}
	return result
}
