package main

func solution(n int, cables [][]int, start int, offline []int) []int {
	neighbors := make([][]int, n+1)
	for _, cable := range cables {
		a, b := cable[0], cable[1]
		neighbors[a] = append(neighbors[a], b) // 케이블은 양쪽 방향이다
		neighbors[b] = append(neighbors[b], a)
	}
	off := make([]bool, n+1) // off[v]: v번 서버가 꺼져 있는가
	for _, server := range offline {
		off[server] = true
	}

	// minute[v]: v번 서버가 파일을 받는 시각. -1은 아직(또는 끝내) 받지 못한 서버
	minute := make([]int, n+1)
	for i := range minute {
		minute[i] = -1
	}
	minute[start] = 0
	queue := []int{start} // Go에는 큐가 없어서 슬라이스와 읽는 위치(head)로 만든다
	for head := 0; head < len(queue); head++ {
		server := queue[head]
		for _, next := range neighbors[server] {
			if minute[next] == -1 && !off[next] { // 꺼진 서버는 받지도 보내지도 않는다
				minute[next] = minute[server] + 1
				queue = append(queue, next)
			}
		}
	}
	latest := -1 // start번 서버가 0분이라 받지 못한 서버(-1)는 가장 큰 값이 되지 않는다
	for _, v := range minute {
		if v > latest {
			latest = v
		}
	}
	count := 0
	for _, v := range minute {
		if v == latest {
			count++
		}
	}
	return []int{latest, count}
}
