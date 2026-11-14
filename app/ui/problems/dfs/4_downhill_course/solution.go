package main

// 재귀로 쓰면 쉼터가 5만 개 한 줄일 때 깊이가 걱정된다. 그래서 재귀 대신,
// '들어갈 때'와 '돌아올 때'를 스택에 따로 넣어 같은 순서를 만든다(돌아올 때는 -번호-1로 구분한다).
func solution(trails [][]int, energy []int, target int) int {
	n := len(energy)
	neighbors := make([][]int, n)
	for _, trail := range trails {
		a, b := trail[0], trail[1]
		neighbors[a] = append(neighbors[a], b) // 어느 쪽이 위쪽인지 모르므로 양쪽에 넣는다
		neighbors[b] = append(neighbors[b], a)
	}
	prefix := make([]int, n) // prefix[v]: 0번부터 v번까지 길 위 energy의 합
	prefix[0] = energy[0]
	// 지금 경로 위의 누적 합이 몇 번씩 있는가. 0번 위(아무 쉼터도 지나지 않은 곳)의 누적 합 0을 넣어 둔다
	onPath := map[int]int{0: 1}
	visited := make([]bool, n)
	visited[0] = true
	count := 0
	stack := []int{0}
	for len(stack) > 0 {
		top := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		if top < 0 {
			hut := -top - 1
			onPath[prefix[hut]]-- // 이 쉼터 아래를 다 보았다: 경로에서 뺀다
			continue
		}
		hut := top
		// u부터 hut까지의 합 = prefix[hut] - (u 바로 위까지의 누적 합). 그 값이 target인 u의 수를 더한다
		count += onPath[prefix[hut]-target] // 없는 키는 0이 나온다
		onPath[prefix[hut]]++
		stack = append(stack, -hut-1) // 아래쪽을 다 본 뒤에 꺼내지도록 먼저 넣는다
		for _, next := range neighbors[hut] {
			if !visited[next] {
				visited[next] = true
				prefix[next] = prefix[hut] + energy[next]
				stack = append(stack, next)
			}
		}
	}
	return count
}
