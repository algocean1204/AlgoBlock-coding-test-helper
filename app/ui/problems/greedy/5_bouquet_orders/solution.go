package main

import (
	"container/heap"
	"sort"
)

// Go의 container/heap은 인터페이스를 채워야 한다. Less가 '크다'를 뜻하게 해서 최대 힙으로 쓴다.
type maxHeap []int

func (h maxHeap) Len() int            { return len(h) }
func (h maxHeap) Less(i, j int) bool  { return h[i] > h[j] }
func (h maxHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *maxHeap) Push(x interface{}) { *h = append(*h, x.(int)) }
func (h *maxHeap) Pop() interface{} {
	old := *h
	last := old[len(old)-1]
	*h = old[:len(old)-1]
	return last
}

func solution(pickup []int, minutes []int, booked []int) []int {
	n := len(pickup)
	must := make([]bool, n) // 꼭 받아야 하는 주문인가
	for _, b := range booked {
		must[b] = true
	}
	order := make([]int, n)
	for i := range order {
		order[i] = i
	}
	sort.Slice(order, func(a, b int) bool { return pickup[order[a]] < pickup[order[b]] }) // 찾으러 오는 시각이 이른 주문부터
	canDrop := &maxHeap{}                                                                  // 되무를 수 있는 받은 주문의 만드는 시간
	count := 0                                                                             // 받은 주문 수
	total := 0                                                                             // 받은 주문을 쉬지 않고 모두 만들면 끝나는 시각 (Go의 int는 64비트)
	for _, i := range order {
		count++
		total += minutes[i]
		if !must[i] {
			heap.Push(canDrop, minutes[i])
		}
		for total > pickup[i] && canDrop.Len() > 0 { // 늦는다: 가장 오래 걸리는 것부터 되무른다
			total -= heap.Pop(canDrop).(int)
			count--
		}
		if total > pickup[i] { // 꼭 받아야 하는 주문끼리도 지킬 수 없다
			return []int{-1, -1}
		}
	}
	return []int{count, total}
}
