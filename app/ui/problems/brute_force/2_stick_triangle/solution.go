package main

func solution(sticks []int) int {
	count := 0
	n := len(sticks)
	for i := 0; i < n; i++ {
		for j := i + 1; j < n; j++ {
			for k := j + 1; k < n; k++ {
				// 세 막대 중 가장 긴 것과 나머지 둘의 합을 비교한다
				longest := sticks[i]
				if sticks[j] > longest {
					longest = sticks[j]
				}
				if sticks[k] > longest {
					longest = sticks[k]
				}
				sum := sticks[i] + sticks[j] + sticks[k] - longest // 가장 긴 것을 뺀 두 막대의 합
				if longest < sum {
					count++
				}
			}
		}
	}
	return count
}
