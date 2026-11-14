package main

import "sort"

func solution(solved []int) int {
	ordered := make([]int, len(solved))
	copy(ordered, solved)
	sort.Sort(sort.Reverse(sort.IntSlice(ordered))) // 많이 푼 회원부터
	level := 0
	for i := 0; i < len(ordered); i++ {
		// 앞에서 i+1명은 모두 ordered[i]문제 이상 풀었다.
		// 그러니 ordered[i] >= i+1이면 'i+1문제 이상 푼 회원이 i+1명 이상'이 된다
		if ordered[i] >= i+1 {
			level = i + 1
		} else {
			break // 여기서 안 되면 더 큰 x도 안 된다
		}
	}
	return level
}
