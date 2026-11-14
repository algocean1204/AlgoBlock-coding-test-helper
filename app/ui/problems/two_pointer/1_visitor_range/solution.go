package main

func solution(visitors []int, queries [][]int) []int {
	// prefix[i]: 1일부터 i일까지 방문자 수의 합. prefix[0]은 아무 날도 더하지 않은 0
	prefix := make([]int, len(visitors)+1)
	for i := 0; i < len(visitors); i++ {
		prefix[i+1] = prefix[i] + visitors[i]
	}
	answer := []int{}
	for _, query := range queries {
		start, end := query[0], query[1]
		answer = append(answer, prefix[end]-prefix[start-1])
	}
	return answer
}
