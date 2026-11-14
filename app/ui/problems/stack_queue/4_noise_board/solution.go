package main

func solution(logs [][]int, window int) []int {
	answer := []int{}
	// 아직 가장 큰 값이 될 수 있는 기록의 번호. 슬라이스와 앞 위치(head)로 덱을 만든다
	// 앞에서 뒤로 갈수록 level이 작다
	candidates := []int{}
	head := 0
	for k, log := range logs {
		time, level := log[0], log[1]
		// 새 기록보다 작거나 같은 옛 기록은 다시는 가장 큰 값이 못 된다: 뒤에서 버린다
		for len(candidates) > head && logs[candidates[len(candidates)-1]][1] <= level {
			candidates = candidates[:len(candidates)-1]
		}
		candidates = append(candidates, k)
		// 창을 벗어난 오래된 기록은 앞에서 뺀다(여러 개일 수 있다). 방금 넣은 기록은 늘 창 안이라 덱이 비지 않는다
		for logs[candidates[head]][0] <= time-window {
			head++
		}
		answer = append(answer, logs[candidates[head]][1])
	}
	return answer
}
