package main

func solution(baked []int, want []int, fresh int) int {
	n := len(baked)
	left := make([]int, n) // left[d]: d일에 구운 빵 가운데 아직 남은 개수
	copy(left, baked)
	oldest := 0 // 아직 남은 빵이 있을 수 있는 가장 오래된 날
	sold := 0
	for day := 0; day < n; day++ {
		oldest = max(oldest, day-fresh+1) // 기한이 지난 날의 빵은 버린다
		need := want[day]
		for need > 0 && oldest <= day { // 가장 오래된 빵부터 판다
			take := min(need, left[oldest])
			left[oldest] -= take
			need -= take
			sold += take
			if left[oldest] == 0 {
				oldest++ // 다 팔린 날은 다시 보지 않는다
			}
		}
	}
	return sold
}
