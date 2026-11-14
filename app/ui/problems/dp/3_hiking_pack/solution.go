package main

func solution(items [][]int, capacity int) int {
	n := len(items)
	// best[i][w]: 앞의 i개 물건만 보고, 무게 합이 w 이하가 되도록 골랐을 때 쓸모 점수 합의 최댓값
	best := make([][]int, n+1)
	for i := range best {
		best[i] = make([]int, capacity+1)
	}
	for i := 1; i <= n; i++ {
		weight, value := items[i-1][0], items[i-1][1]
		for w := 0; w <= capacity; w++ {
			best[i][w] = best[i-1][w] // i번째 물건을 넣지 않는다
			if weight <= w {          // i번째 물건을 넣는다: 나머지 무게 w - weight는 앞의 물건들로 채운다
				best[i][w] = max(best[i][w], best[i-1][w-weight]+value)
			}
		}
	}
	return best[n][capacity]
}
