package main

import "sort"

// 재귀 대신 반복문: 긴 줄 입력에서 깊어지지 않게
func find(parent []int, x int) int {
	for parent[x] != x {
		parent[x] = parent[parent[x]] // 경로 압축
		x = parent[x]
	}
	return x
}

func solution(n int, roads [][]int) int {
	parent := make([]int, n+1)
	for i := range parent {
		parent[i] = i
	}

	// 싼 길부터 본다
	sort.Slice(roads, func(p, q int) bool { return roads[p][2] < roads[q][2] })

	total := 0
	paved := 0
	for _, r := range roads {
		rootA := find(parent, r[0])
		rootB := find(parent, r[1])
		if rootA == rootB { // 이미 오갈 수 있다: 포장하면 고리가 생긴다
			continue
		}
		parent[rootB] = rootA
		total += r[2]
		paved++
	}

	if paved < n-1 { // 다 보고도 길이 n-1개가 안 되면 묶음이 둘 이상 남았다
		return -1
	}
	return total
}
