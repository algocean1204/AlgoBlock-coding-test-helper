package main

func solution(n int, tracks [][]int, queries [][]int) []int {
	const INF = 1000000000 // 가장 긴 최단 시간(299,000)보다 크다. Go의 int는 64비트라 두 번 더해도 넘치지 않는다
	dist := make([][]int, n+1)
	for i := range dist {
		dist[i] = make([]int, n+1)
		for j := range dist[i] {
			dist[i][j] = INF
		}
	}
	for s := 1; s <= n; s++ {
		dist[s][s] = 0
	}
	for _, t := range tracks {
		if t[2] < dist[t[0]][t[1]] { // 같은 두 역 사이 선로가 여럿이면 짧은 것만 남긴다
			dist[t[0]][t[1]] = t[2]
			dist[t[1]][t[0]] = t[2]
		}
	}

	asked := make([][]int, n+1) // asked[k]: k번 역까지 열렸을 때를 묻는 질문의 번호들
	for i, q := range queries {
		asked[q[0]] = append(asked[q[0]], i)
	}

	answer := make([]int, len(queries))
	for k := 1; k <= n; k++ {
		// 플로이드: k번 역을 거쳐 가는 길로 모든 두 역 사이 거리를 고친다(아직 닫힌 역까지의 거리도 고쳐 둔다)
		for i := 1; i <= n; i++ {
			for j := 1; j <= n; j++ {
				if dist[i][k]+dist[k][j] < dist[i][j] {
					dist[i][j] = dist[i][k] + dist[k][j]
				}
			}
		}
		// 이제 dist[a][b]는 1~k번 역만 거쳐 가는 가장 짧은 시간이다
		for _, idx := range asked[k] {
			d := dist[queries[idx][1]][queries[idx][2]]
			if d >= INF {
				answer[idx] = -1
			} else {
				answer[idx] = d
			}
		}
	}
	return answer
}
