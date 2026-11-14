package main

import (
	"container/heap"
	"strconv"
)

// Go에는 만들어진 힙이 없다. container/heap이 요구하는 메서드 다섯 개를 구현한다
type MaxHeap []int

func (h MaxHeap) Len() int           { return len(h) }
func (h MaxHeap) Less(i, j int) bool { return h[i] > h[j] } // 큰 것이 꼭대기: 최대 힙. 부호를 뒤집을 필요가 없다
func (h MaxHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *MaxHeap) Push(x any)        { *h = append(*h, x.(int)) }
func (h *MaxHeap) Pop() any {
	old := *h
	last := old[len(old)-1]
	*h = old[:len(old)-1]
	return last
}

func solution(records []string, k int) int {
	fastest := &MaxHeap{} // 지금까지 가장 빠른 기록 k개. 가장 느린 기록(k위)이 꼭대기에 온다
	alerts := 0
	for _, record := range records {
		minutes, _ := strconv.Atoi(record[:2])
		seconds, _ := strconv.Atoi(record[3:])
		time := minutes*60 + seconds
		if fastest.Len() < k {
			alerts++
			heap.Push(fastest, time)
		} else if time < (*fastest)[0] { // 지금 k위보다 빨라야 한다. 같으면 먼저 들어온 기록이 앞선다
			alerts++
			heap.Pop(fastest)
			heap.Push(fastest, time)
		}
	}
	return alerts
}
