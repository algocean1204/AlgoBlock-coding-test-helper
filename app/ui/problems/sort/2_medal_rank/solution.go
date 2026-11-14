package main

import "sort"

func solution(classes []string, medals [][]int) []string {
	n := len(classes)
	// 반 번호(0..n-1)를 줄 세운다. 정렬 기준은 금 많은 순 → 은 많은 순 → 동 많은 순 → 이름 사전 순
	order := make([]int, n)
	for i := 0; i < n; i++ {
		order[i] = i
	}
	sort.Slice(order, func(x, y int) bool {
		a, b := order[x], order[y]
		// 메달은 많은 쪽이 앞(내림차순)이라 > 로 비교한다
		for j := 0; j < 3; j++ {
			if medals[a][j] != medals[b][j] {
				return medals[a][j] > medals[b][j]
			}
		}
		return classes[a] < classes[b] // 이름은 사전 순(오름차순). 앞이어야 true
	})
	answer := []string{}
	for _, i := range order {
		answer = append(answer, classes[i])
	}
	return answer
}
