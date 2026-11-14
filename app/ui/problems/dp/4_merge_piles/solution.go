package main

import "math"

func solution(piles []int) int {
	n := len(piles)
	prefix := make([]int, n+1) // prefix[i]: piles[0] ~ piles[i - 1]의 합
	for i := 0; i < n; i++ {
		prefix[i+1] = prefix[i] + piles[i]
	}
	cost := make([][]int, n) // cost[i][j]: i ~ j번째 더미를 한 더미로 만드는 최소 시간
	for i := range cost {
		cost[i] = make([]int, n)
	}
	for length := 2; length <= n; length++ { // 짧은 구간부터 채운다
		for i := 0; i+length-1 < n; i++ {
			j := i + length - 1
			best := math.MaxInt
			for k := i; k < j; k++ { // 마지막에 [i, k] 더미와 [k + 1, j] 더미를 합친다
				best = min(best, cost[i][k]+cost[k+1][j])
			}
			cost[i][j] = best + prefix[j+1] - prefix[i] // 마지막 합치기에 드는 시간 = 구간 전체의 자루 수
		}
	}
	return cost[0][n-1]
}
