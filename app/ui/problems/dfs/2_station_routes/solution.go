package main

func solution(rails [][]int) int {
	n := len(rails)
	onRoute := make([]bool, n) // 지금 만들고 있는 길 위에 있는 역

	// station까지 왔을 때, 여기서 n - 1번 역까지 이어 갈 수 있는 길의 수
	var countFrom func(station int) int
	countFrom = func(station int) int {
		if station == n-1 {
			return 1 // 도착: 길 하나가 완성되고 여기서 끝난다
		}
		routes := 0
		for next := 0; next < n; next++ {
			if rails[station][next] == 1 && !onRoute[next] {
				onRoute[next] = true // 들어갈 때 표시한다
				routes += countFrom(next)
				onRoute[next] = false // 돌아올 때 지운다: 다른 갈래에서 이 역을 다시 쓸 수 있게
			}
		}
		return routes
	}

	onRoute[0] = true // 출발역도 길 위에 있다
	return countFrom(0)
}
