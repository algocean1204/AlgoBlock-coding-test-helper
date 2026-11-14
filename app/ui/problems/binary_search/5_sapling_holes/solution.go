package main

import "sort"

// 모든 간격을 gap 이상으로 둘 때 심을 수 있는 묘목의 수
func planted(trees []int, holes []int, gap int) int {
	count := 0
	last := -1000000000 // 지금 보는 구덩이 바로 앞에 있는 나무(없으면 아주 먼 곳)
	i := 0              // trees[i]: 지금 보는 구덩이 뒤에 오는 첫 큰 나무
	for _, hole := range holes {
		for i < len(trees) && trees[i] < hole { // 구덩이보다 앞에 있는 큰 나무를 지나간다
			last = trees[i]
			i++
		}
		nextTree := 2000000000 // 뒤에 큰 나무가 없으면 아주 먼 곳
		if i < len(trees) {
			nextTree = trees[i]
		}
		// 앞 나무와도, 뒤에 오는 큰 나무와도 gap 이상 떨어져야 심는다
		if hole-last >= gap && nextTree-hole >= gap {
			count++
			last = hole
		}
	}
	return count
}

func solution(trees []int, holes []int, count int) int {
	sortedTrees := append([]int(nil), trees...)
	sortedHoles := append([]int(nil), holes...)
	sort.Ints(sortedTrees)
	sort.Ints(sortedHoles)
	high := sortedTrees[len(sortedTrees)-1]
	if sortedHoles[len(sortedHoles)-1] > high {
		high = sortedHoles[len(sortedHoles)-1]
	}
	low := sortedTrees[0]
	if sortedHoles[0] < low {
		low = sortedHoles[0]
	}
	left := 1
	right := high - low
	for i := 0; i+1 < len(sortedTrees); i++ { // 큰 나무끼리의 간격은 바꿀 수 없으므로 답은 이보다 클 수 없다
		if sortedTrees[i+1]-sortedTrees[i] < right {
			right = sortedTrees[i+1] - sortedTrees[i]
		}
	}
	answer := 1
	for left <= right {
		mid := (left + right) / 2
		if planted(sortedTrees, sortedHoles, mid) >= count { // 더 많이 심을 수 있으면 몇 그루를 덜 심으면 된다
			answer = mid
			left = mid + 1
		} else {
			right = mid - 1
		}
	}
	return answer
}
