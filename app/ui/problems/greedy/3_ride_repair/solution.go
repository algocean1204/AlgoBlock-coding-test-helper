package main

import "sort"

func solution(fix []int, line []int, walk int) int64 {
	n := len(fix)
	order := make([]int, n)
	for i := range order {
		order[i] = i
	}
	// a 다음에 b를 고치면 b의 손님이 (fix[a] + walk) × line[b]만큼 더 기다리고,
	// b 다음에 a를 고치면 a의 손님이 (fix[b] + walk) × line[a]만큼 더 기다린다 → 작은 쪽 차례가 앞
	sort.Slice(order, func(i, j int) bool {
		a, b := order[i], order[j]
		return (fix[a]+walk)*line[b] < (fix[b]+walk)*line[a]
	})

	var now int64 = 0   // 지금 시각
	var total int64 = 0 // 기다림의 합 (int32를 넘을 수 있다)
	for k, ride := range order {
		if k > 0 {
			now += int64(walk) // 다음 놀이기구까지 걸어간다(첫 놀이기구는 걷지 않는다)
		}
		now += int64(fix[ride]) // 이 놀이기구를 다 고친 시각
		total += now * int64(line[ride])
	}
	return total
}
