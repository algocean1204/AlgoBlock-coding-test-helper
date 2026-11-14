package main

import "sort"

func solution(rows int, apples [][]int, k int) []int {
	kindsOf := make([]map[int]bool, rows+1) // kindsOf[줄 번호] = 그 줄의 서로 다른 무게(0번 칸은 쓰지 않는다)
	for row := range kindsOf {
		kindsOf[row] = map[int]bool{}
	}
	for _, apple := range apples {
		kindsOf[apple[0]][apple[1]] = true // 같은 무게는 한 번만
	}

	answer := []int{}
	for row := 1; row <= rows; row++ {
		kinds := []int{}
		for weight := range kindsOf[row] {
			kinds = append(kinds, weight)
		}
		sort.Sort(sort.Reverse(sort.IntSlice(kinds))) // 무거운 것부터
		// k번째 무게는 위치 k-1. 적은 무게가 k개보다 적으면 -1(사과가 없는 줄 포함)
		if k <= len(kinds) {
			answer = append(answer, kinds[k-1])
		} else {
			answer = append(answer, -1)
		}
	}
	return answer
}
