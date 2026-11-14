package main

import "container/heap"

// Go에는 만들어진 힙이 없다. container/heap이 요구하는 메서드 다섯 개를 구현한다
// less 함수를 바꿔 끼우면 같은 타입으로 최소 힙과 최대 힙을 둘 다 만든다
type Heap struct {
	items []int
	less  func(a, b int) bool
}

func (h Heap) Len() int           { return len(h.items) }
func (h Heap) Less(i, j int) bool { return h.less(h.items[i], h.items[j]) }
func (h Heap) Swap(i, j int)      { h.items[i], h.items[j] = h.items[j], h.items[i] }
func (h *Heap) Push(x any)        { h.items = append(h.items, x.(int)) }
func (h *Heap) Pop() any {
	last := h.items[len(h.items)-1]
	h.items = h.items[:len(h.items)-1]
	return last
}

func solution(houses []int) int64 {
	// 작은 쪽 절반: 큰 값이 꼭대기에 오게 > 로 비교한다(최대 힙). 부호를 뒤집을 필요가 없다
	low := &Heap{less: func(a, b int) bool { return a > b }}
	// 큰 쪽 절반: 작은 값이 꼭대기에 온다(최소 힙)
	high := &Heap{less: func(a, b int) bool { return a < b }}
	lowSum := 0 // Go의 int는 64비트라 넘치지 않는다
	highSum := 0
	var total int64 = 0
	for _, house := range houses {
		if low.Len() == 0 || house <= low.items[0] {
			heap.Push(low, house)
			lowSum += house
		} else {
			heap.Push(high, house)
			highSum += house
		}
		// 개수 맞추기: low가 high와 같거나 하나 더 많게 둔다. 그러면 low의 꼭대기가 가운데 값이다
		if low.Len() > high.Len()+1 {
			moved := heap.Pop(low).(int)
			lowSum -= moved
			heap.Push(high, moved)
			highSum += moved
		} else if high.Len() > low.Len() {
			moved := heap.Pop(high).(int)
			highSum -= moved
			heap.Push(low, moved)
			lowSum += moved
		}
		middle := low.items[0]
		// (작은 쪽 집들에서 가운데까지의 거리 합) + (큰 쪽 집들에서 가운데까지의 거리 합)
		total += int64((middle*low.Len() - lowSum) + (highSum - middle*high.Len()))
	}
	return total
}
