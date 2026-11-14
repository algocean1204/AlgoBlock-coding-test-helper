package main

import "container/heap"

// Go의 container/heap은 Len, Less, Swap, Push, Pop을 직접 만들어 줘야 한다.
type Item struct{ h, r, c int }
type MinHeap []Item

func (q MinHeap) Len() int            { return len(q) }
func (q MinHeap) Less(i, j int) bool  { return q[i].h < q[j].h } // 턱이 낮은 것이 위로
func (q MinHeap) Swap(i, j int)       { q[i], q[j] = q[j], q[i] }
func (q *MinHeap) Push(x interface{}) { *q = append(*q, x.(Item)) }
func (q *MinHeap) Pop() interface{} {
	old := *q
	item := old[len(old)-1]
	*q = old[:len(old)-1]
	return item
}

func solution(ground [][]int) int {
	rows, cols := len(ground), len(ground[0])
	const INF = 1 << 60
	highest := make([][]int, rows) // 그 칸까지 가는 길에서 넘는 가장 높은 턱의 최솟값
	for i := range highest {
		highest[i] = make([]int, cols)
		for j := range highest[i] {
			highest[i][j] = INF
		}
	}
	highest[0][0] = 0
	q := &MinHeap{{0, 0, 0}}
	dr := []int{-1, 1, 0, 0}
	dc := []int{0, 0, -1, 1}
	for q.Len() > 0 {
		top := heap.Pop(q).(Item)
		h, r, c := top.h, top.r, top.c
		if h > highest[r][c] {
			continue
		}
		if r == rows-1 && c == cols-1 {
			return h
		}
		for k := 0; k < 4; k++ {
			nr, nc := r+dr[k], c+dc[k]
			if nr >= 0 && nr < rows && nc >= 0 && nc < cols {
				ledge := ground[nr][nc] - ground[r][c]
				if ledge < 0 { // Go에는 정수용 절댓값 함수가 없다
					ledge = -ledge
				}
				cur := h
				if ledge > cur { // 합이 아니라 가장 높은 턱
					cur = ledge
				}
				if cur < highest[nr][nc] {
					highest[nr][nc] = cur
					heap.Push(q, Item{cur, nr, nc})
				}
			}
		}
	}
	return highest[rows-1][cols-1]
}
