package main

import "sort"

// values에서 x 이상인 값이 처음 나오는 자리(없으면 길이)
func firstAtLeast(values []int, x int) int {
	left := 0
	right := len(values)
	for left < right {
		mid := (left + right) / 2
		if values[mid] >= x {
			right = mid
		} else {
			left = mid + 1
		}
	}
	return left
}

func solution(prices []int, ranges [][]int) []int {
	sorted := make([]int, len(prices))
	copy(sorted, prices)
	sort.Ints(sorted)
	answer := []int{}
	for _, r := range ranges {
		low := r[0]
		high := r[1]
		start := firstAtLeast(sorted, low)
		// 가격이 정수라서 'high보다 큰 값이 처음 나오는 자리' = 'high + 1 이상이 처음 나오는 자리'
		end := firstAtLeast(sorted, high+1)
		answer = append(answer, end-start)
	}
	return answer
}
