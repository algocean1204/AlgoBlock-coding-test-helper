package main

import "container/heap"

const INF = int64(1) << 60 // 시간 합이 int32를 넘으므로 int64, 더해도 넘치지 않게 넉넉히

type item struct {
	dist int64
	town int
}

type minHeap []item

func (h minHeap) Len() int            { return len(h) }
func (h minHeap) Less(i, j int) bool  { return h[i].dist < h[j].dist }
func (h minHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *minHeap) Push(x interface{}) { *h = append(*h, x.(item)) }
func (h *minHeap) Pop() interface{} {
	old := *h
	top := old[len(old)-1]
	*h = old[:len(old)-1]
	return top
}

type edge struct {
	to   int
	time int64
}

func dijkstra(graph [][]edge, n, start int) []int64 {
	dist := make([]int64, n+1)
	for i := range dist {
		dist[i] = INF
	}
	dist[start] = 0
	h := &minHeap{{0, start}}
	for h.Len() > 0 {
		top := heap.Pop(h).(item)
		if top.dist > dist[top.town] {
			continue
		}
		for _, e := range graph[top.town] {
			if top.dist+e.time < dist[e.to] {
				dist[e.to] = top.dist + e.time
				heap.Push(h, item{dist[e.to], e.to})
			}
		}
	}
	return dist
}

func solution(n int, roads [][]int, farms []int, market int) int64 {
	small := make([][]edge, n+1)   // 작은 트럭: u → v, slow분
	bigBack := make([][]edge, n+1) // 큰 트럭의 도로를 거꾸로 뒤집은 것: v → u, fast분
	for _, r := range roads {
		small[r[0]] = append(small[r[0]], edge{r[1], int64(r[2])})
		bigBack[r[1]] = append(bigBack[r[1]], edge{r[0], int64(r[3])})
	}

	// 뒤집은 그래프에서 시장으로부터의 거리 = 각 마을에서 시장까지 큰 트럭이 걸리는 시간
	toMarket := dijkstra(bigBack, n, market)

	gather := make([]int64, n+1) // gather[m]: 작은 트럭이 모두 m번 마을에 모이는 시각(가장 늦게 도착한 트럭)
	for _, farm := range farms {
		arrive := dijkstra(small, n, farm)
		for m := 1; m <= n; m++ {
			if arrive[m] > gather[m] {
				gather[m] = arrive[m]
			}
		}
	}

	answer := INF
	for m := 1; m <= n; m++ { // 모이는 마을을 모두 해 본다. 닿지 못하는 곳은 무한대라 뽑히지 않는다
		if gather[m] < INF && toMarket[m] < INF && gather[m]+toMarket[m] < answer {
			answer = gather[m] + toMarket[m]
		}
	}
	if answer == INF {
		return -1
	}
	return answer
}
