package main

import (
	"container/heap"
	"sort"
)

// Go에는 만들어진 힙이 없다. container/heap이 요구하는 메서드 다섯 개를 구현한다
// 원소는 {도착 시각, 진료 시간, 위급도, 번호}. 위급도는 큰 것, 진료 시간은 짧은 것, 번호는 작은 것이 꼭대기에 온다
type PetHeap [][4]int

func (h PetHeap) Len() int { return len(h) }
func (h PetHeap) Less(i, j int) bool {
	if h[i][2] != h[j][2] {
		return h[i][2] > h[j][2]
	}
	if h[i][1] != h[j][1] {
		return h[i][1] < h[j][1]
	}
	return h[i][3] < h[j][3]
}
func (h PetHeap) Swap(i, j int) { h[i], h[j] = h[j], h[i] }
func (h *PetHeap) Push(x any)   { *h = append(*h, x.([4]int)) }
func (h *PetHeap) Pop() any {
	old := *h
	last := old[len(old)-1]
	*h = old[:len(old)-1]
	return last
}

func solution(patients [][]int) int64 {
	n := len(patients)
	arrivals := make([][4]int, n) // {도착 시각, 진료 시간, 위급도, 번호}
	for i, p := range patients {
		arrivals[i] = [4]int{p[0], p[1], p[2], i}
	}
	sort.Slice(arrivals, func(a, b int) bool { return arrivals[a][0] < arrivals[b][0] }) // 도착 시각 순
	waiting := &PetHeap{} // 도착한 동물
	time := 0
	nextArrival := 0 // arrivals에서 아직 힙에 넣지 않은 첫 자리
	var total int64 = 0
	for count := 0; count < n; count++ {
		if waiting.Len() == 0 && arrivals[nextArrival][0] > time {
			time = arrivals[nextArrival][0] // 도착한 동물이 없으면 다음 동물이 올 때까지 건너뛴다
		}
		for nextArrival < n && arrivals[nextArrival][0] <= time {
			heap.Push(waiting, arrivals[nextArrival])
			nextArrival++
		}
		pet := heap.Pop(waiting).([4]int)
		total += int64(time - pet[0])
		time += pet[1]
	}
	return total
}
