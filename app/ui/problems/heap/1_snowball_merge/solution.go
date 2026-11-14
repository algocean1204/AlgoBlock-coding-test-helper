package main

import "container/heap"

// Go에는 만들어진 힙이 없다. container/heap이 요구하는 메서드 다섯 개를 구현한다
type IntHeap []int

func (h IntHeap) Len() int           { return len(h) }
func (h IntHeap) Less(i, j int) bool { return h[i] < h[j] } // 작은 것이 꼭대기: 최소 힙
func (h IntHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *IntHeap) Push(x any)        { *h = append(*h, x.(int)) }
func (h *IntHeap) Pop() any {
	old := *h
	last := old[len(old)-1]
	*h = old[:len(old)-1]
	return last
}

func solution(snowballs []int) int64 {
	h := IntHeap(append([]int{}, snowballs...))
	heap.Init(&h)
	var total int64 = 0 // Go의 int는 64비트지만 반환 형이 int64다
	for h.Len() > 1 {
		lightest := heap.Pop(&h).(int)
		second := heap.Pop(&h).(int)
		merged := lightest + second
		total += int64(merged)
		heap.Push(&h, merged)
	}
	return total
}

