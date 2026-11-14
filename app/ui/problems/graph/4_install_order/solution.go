package main

import "container/heap"

// Go의 힙은 인터페이스를 채워 써야 한다. Less가 작은 것이 먼저 나오게 한다.
type minHeap []int

func (h minHeap) Len() int            { return len(h) }
func (h minHeap) Less(i, j int) bool  { return h[i] < h[j] }
func (h minHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *minHeap) Push(x interface{}) { *h = append(*h, x.(int)) }
func (h *minHeap) Pop() interface{} {
	old := *h
	last := old[len(old)-1]
	*h = old[:len(old)-1]
	return last
}

func solution(n int, rules [][]int) []int {
	after := make([][]int, n+1) // after[a]: a를 설치해야 설치할 수 있는 패키지들
	waiting := make([]int, n+1) // waiting[b]: b보다 먼저 설치해야 하는데 아직 설치하지 않은 패키지 수(진입 차수)
	for _, r := range rules {
		after[r[0]] = append(after[r[0]], r[1])
		waiting[r[1]]++
	}

	ready := &minHeap{}
	for p := 1; p <= n; p++ {
		if waiting[p] == 0 {
			heap.Push(ready, p)
		}
	}
	order := []int{}
	for ready.Len() > 0 {
		pkg := heap.Pop(ready).(int)
		order = append(order, pkg)
		for _, nxt := range after[pkg] {
			waiting[nxt]--
			if waiting[nxt] == 0 {
				heap.Push(ready, nxt)
			}
		}
	}

	if len(order) < n { // 끝내 설치할 수 없는 패키지가 남았다: 규칙에 사이클이 있다
		return []int{}
	}
	return order
}
