package main

import "container/heap"

// Go의 container/heap은 Len, Less, Swap, Push, Pop을 직접 만들어 줘야 한다.
type Item struct{ d, v int }
type MinHeap []Item

func (h MinHeap) Len() int            { return len(h) }
func (h MinHeap) Less(i, j int) bool  { return h[i].d < h[j].d } // 시간이 작은 것이 위로
func (h MinHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *MinHeap) Push(x interface{}) { *h = append(*h, x.(Item)) }
func (h *MinHeap) Pop() interface{} {
	old := *h
	item := old[len(old)-1]
	*h = old[:len(old)-1]
	return item
}

type Edge struct{ to, time int }

func solution(n int, roads [][]int) []int {
	graph := make([][]Edge, n+1)
	for _, road := range roads {
		a, b, time := road[0], road[1], road[2]
		graph[a] = append(graph[a], Edge{b, time})
		graph[b] = append(graph[b], Edge{a, time})
	}

	const INF = 1 << 60
	dist := make([]int, n+1)
	for i := range dist {
		dist[i] = INF
	}
	dist[1] = 0
	h := &MinHeap{{0, 1}}
	for h.Len() > 0 {
		top := heap.Pop(h).(Item)
		d, now := top.d, top.v
		if d > dist[now] { // 이미 더 짧은 시간으로 확정된 마을
			continue
		}
		for _, e := range graph[now] {
			if d+e.time < dist[e.to] {
				dist[e.to] = d + e.time
				heap.Push(h, Item{dist[e.to], e.to})
			}
		}
	}
	return dist[1:]
}
