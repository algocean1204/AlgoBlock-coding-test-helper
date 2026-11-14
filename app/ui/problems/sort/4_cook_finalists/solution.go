package main

import "sort"

func solution(taste []int, look []int) int {
	people := [][2]int{} // (맛, 모양)
	for i := 0; i < len(taste); i++ {
		people = append(people, [2]int{taste[i], look[i]})
	}
	// 맛 점수가 높은 사람부터 본다. 맛 점수가 같으면 모양 점수가 낮은 사람부터 본다.
	// 같은 맛 점수끼리는 서로 떨어뜨리지 못하므로, 같은 무리에서 모양 점수가 높은 사람이
	// 먼저 지나가 bestLook을 올려 두면 안 된다.
	sort.Slice(people, func(a, b int) bool {
		if people[a][0] != people[b][0] {
			return people[a][0] > people[b][0] // 맛은 내림차순
		}
		return people[a][1] < people[b][1] // 모양은 오름차순
	})

	bestLook := -1 // 지금까지 지나간 사람들의 모양 점수 가운데 가장 높은 값
	count := 0
	for _, p := range people {
		myLook := p[1]
		// 앞에 지나간 사람은 나보다 맛 점수가 높거나, 같은 맛 점수에 모양 점수가 나 이하다.
		// 그러니 bestLook이 내 모양 점수보다 높으면, 맛도 모양도 나보다 높은 사람이 있다는 뜻이다.
		if bestLook <= myLook {
			count++
		}
		if myLook > bestLook {
			bestLook = myLook
		}
	}
	return count
}
