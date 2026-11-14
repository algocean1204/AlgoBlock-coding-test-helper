package main

import "container/heap"

// Go의 container/heap은 Len, Less, Swap, Push, Pop을 직접 만들어 줘야 한다.
type Item struct{ cost, city, used, just int }
type MinHeap []Item

func (h MinHeap) Len() int            { return len(h) }
func (h MinHeap) Less(i, j int) bool  { return h[i].cost < h[j].cost } // 통행료가 작은 것이 위로
func (h MinHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *MinHeap) Push(x interface{}) { *h = append(*h, x.(Item)) }
func (h *MinHeap) Pop() interface{} {
	old := *h
	item := old[len(old)-1]
	*h = old[:len(old)-1]
	return item
}

type Edge struct{ to, toll int }

func solution(n int, roads [][]int, k int) int {
	graph := make([][]Edge, n+1)
	for _, road := range roads {
		u, v, toll := road[0], road[1], road[2]
		graph[u] = append(graph[u], Edge{v, toll})
		graph[v] = append(graph[v], Edge{u, toll})
	}

	const INF = 1 << 60
	// dist[city][used][just]: 통행권을 used장 쓰고 city에 왔을 때 낸 통행료 합의 최솟값
	// just는 바로 앞 도로에 통행권을 썼으면 1, 통행료를 냈으면(또는 아직 출발 전이면) 0
	dist := make([][][2]int, n+1)
	for i := range dist {
		dist[i] = make([][2]int, k+1)
		for j := range dist[i] {
			dist[i][j] = [2]int{INF, INF}
		}
	}
	dist[1][0][0] = 0
	h := &MinHeap{{0, 1, 0, 0}}
	for h.Len() > 0 {
		top := heap.Pop(h).(Item)
		cost, city, used, just := top.cost, top.city, top.used, top.just
		if cost > dist[city][used][just] {
			continue
		}
		if city == n { // 몇 장을 썼든 n번 도시를 처음 꺼낸 값이 가장 싸다(통행권은 남겨도 된다)
			return cost
		}
		for _, e := range graph[city] {
			if cost+e.toll < dist[e.to][used][0] { // 통행료를 낸다
				dist[e.to][used][0] = cost + e.toll
				heap.Push(h, Item{cost + e.toll, e.to, used, 0})
			}
			if used < k && just == 0 && cost < dist[e.to][used+1][1] { // 통행권을 쓴다(바로 앞 도로에 쓰지 않았을 때만)
				dist[e.to][used+1][1] = cost
				heap.Push(h, Item{cost, e.to, used + 1, 1})
			}
		}
	}
	return -1
}
