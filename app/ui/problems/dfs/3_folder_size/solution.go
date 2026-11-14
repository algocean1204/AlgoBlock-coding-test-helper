package main

// 재귀로 쓰면 폴더가 10만 겹일 때 깊이가 걱정된다. 그래서 바깥에서 안쪽으로 방문한 순서를 스택으로 구하고
// 그 순서를 거꾸로 따라가며 더한다(안쪽이 먼저 끝난다).
func solution(parent []int, files []int, limit int) int {
	n := len(parent)
	children := make([][]int, n)
	for folder := 0; folder < n; folder++ {
		if parent[folder] != -1 {
			children[parent[folder]] = append(children[parent[folder]], folder)
		}
	}
	// 0번에서 출발해 바깥에서 안쪽으로 방문한 순서를 적는다(재귀 대신 스택)
	order := []int{}
	stack := []int{0}
	for len(stack) > 0 {
		folder := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		order = append(order, folder)
		stack = append(stack, children[folder]...)
	}
	// 이 순서를 거꾸로 보면 안쪽 폴더가 언제나 바깥 폴더보다 먼저 나온다
	total := append([]int{}, files...)
	for i := n - 1; i >= 0; i-- {
		folder := order[i]
		if parent[folder] != -1 {
			total[parent[folder]] += total[folder]
		}
	}
	count := 0
	for _, size := range total {
		if size >= limit {
			count++
		}
	}
	return count
}
