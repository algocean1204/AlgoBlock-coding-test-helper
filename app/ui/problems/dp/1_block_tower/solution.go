package main

func solution(n int) int64 {
	// 탑의 수는 int32 범위를 넘으므로 int64로 담는다
	ways := make([]int64, n+1) // ways[h]: 높이가 정확히 h인 탑의 수
	ways[0] = 1                // 아무것도 쌓지 않은 높이 0의 탑 하나
	for height := 1; height <= n; height++ {
		for block := 1; block <= 3; block++ { // 맨 위에 놓은 블록의 높이
			if height-block >= 0 {
				ways[height] += ways[height-block]
			}
		}
	}
	return ways[n]
}
