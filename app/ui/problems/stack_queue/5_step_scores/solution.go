package main

func solution(scores []int, jump int) int64 {
	n := len(scores)
	best := make([]int64, n) // best[i]: i번 돌에 섰을 때까지 모은 점수의 가장 큰 값
	best[0] = int64(scores[0])
	// 바로 앞 jump개 돌의 번호. 슬라이스와 앞 위치(head)로 덱을 만든다. 앞에서 뒤로 갈수록 best가 작다
	window := []int{0}
	head := 0
	for i := 1; i < n; i++ {
		// i번 돌로 한 번에 올 수 없는 돌(jump칸보다 먼 돌)은 앞에서 뺀다
		for window[head] < i-jump {
			head++
		}
		best[i] = int64(scores[i]) + best[window[head]]
		// best[i]보다 작거나 같은 돌은 앞으로 고를 일이 없다: 뒤에서 버린다
		for len(window) > head && best[window[len(window)-1]] <= best[i] {
			window = window[:len(window)-1]
		}
		window = append(window, i)
	}
	return best[n-1]
}
