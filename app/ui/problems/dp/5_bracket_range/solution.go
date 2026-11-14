package main

import "math"

func solution(values []int, signs string) []int {
	n := len(values)
	big := make([][]int, n)   // big[i][j]: values[i] ~ values[j]를 괄호로 묶어 만들 수 있는 가장 큰 값
	small := make([][]int, n) // small[i][j]: 같은 구간의 가장 작은 값
	for i := 0; i < n; i++ {
		big[i] = make([]int, n)
		small[i] = make([]int, n)
		big[i][i] = values[i]
		small[i][i] = values[i]
	}
	for length := 2; length <= n; length++ { // 짧은 구간부터 채운다
		for i := 0; i+length-1 < n; i++ {
			j := i + length - 1
			best := math.MinInt
			worst := math.MaxInt
			for k := i; k < j; k++ { // signs[k]를 맨 마지막에 계산한다: [i, k]와 [k + 1, j]로 나뉜다
				var high, low int
				if signs[k] == '+' {
					high = big[i][k] + big[k+1][j]
					low = small[i][k] + small[k+1][j]
				} else if signs[k] == '-' {
					high = big[i][k] - small[k+1][j] // 빼는 쪽은 가장 작을 때 결과가 가장 크다
					low = small[i][k] - big[k+1][j]
				} else { // '^': 두 값 가운데 큰 값
					high = max(big[i][k], big[k+1][j])
					low = max(small[i][k], small[k+1][j]) // 큰 값을 작게 하려면 양쪽을 모두 작게 한다
				}
				best = max(best, high)
				worst = min(worst, low)
			}
			big[i][j] = best
			small[i][j] = worst
		}
	}
	return []int{big[0][n-1], small[0][n-1]}
}
