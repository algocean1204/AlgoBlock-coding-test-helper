package main

import (
	"container/heap"
	"strconv"
	"strings"
)

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

type Edge struct{ to, minutes int }

func solution(routes []string, start string, goal string) int {
	// 선착장 이름마다 0부터 번호를 매기고, 번호로 인접 목록을 만든다
	id := map[string]int{}
	graph := [][]Edge{}
	getID := func(name string) int {
		if _, ok := id[name]; !ok {
			id[name] = len(id)
			graph = append(graph, nil)
		}
		return id[name]
	}
	for _, route := range routes {
		part := strings.Split(route, " ")
		minutes, _ := strconv.Atoi(part[2])
		from := getID(part[0])
		to := getID(part[1])
		graph[from] = append(graph[from], Edge{to, minutes})
	}

	source, target := id[start], id[goal]
	const INF = 1 << 60
	dist := make([]int, len(id))
	for i := range dist {
		dist[i] = INF
	}
	dist[source] = 0
	h := &MinHeap{{0, source}}
	for h.Len() > 0 {
		top := heap.Pop(h).(Item)
		d, now := top.d, top.v
		if d > dist[now] { // 이미 더 빠른 시간으로 확정된 선착장
			continue
		}
		if now == target { // 도착점은 큐에서 꺼낼 때 확정된다
			return d
		}
		for _, e := range graph[now] {
			if d+e.minutes < dist[e.to] {
				dist[e.to] = d + e.minutes
				heap.Push(h, Item{dist[e.to], e.to})
			}
		}
	}
	return -1
}
