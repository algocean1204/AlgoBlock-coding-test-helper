package main

func solution(rows int, cols int, start []int, commands string) []int {
	row, col := start[0], start[1]
	for _, command := range commands {
		dr, dc := 0, 0
		if command == 'N' {
			dr = -1
		} else if command == 'S' {
			dr = 1
		} else if command == 'W' {
			dc = -1
		} else {
			dc = 1
		}
		nextRow, nextCol := row+dr, col+dc
		if nextRow >= 0 && nextRow < rows && nextCol >= 0 && nextCol < cols {
			row, col = nextRow, nextCol
		}
	}
	return []int{row, col}
}
