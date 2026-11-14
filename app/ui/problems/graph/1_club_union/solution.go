package main

// find를 재귀로 쓰면 긴 줄 입력에서 깊어지므로 반복문으로 쓴다
func find(parent []int, x int) int {
	for parent[x] != x {
		parent[x] = parent[parent[x]] // 경로 압축: 한 칸 위를 건너뛰어 대표에 가깝게 고쳐 둔다
		x = parent[x]
	}
	return x
}

func solution(n int, merges [][]int) int {
	parent := make([]int, n+1)
	for i := range parent {
		parent[i] = i
	}

	groups := n
	for _, m := range merges {
		rootA := find(parent, m[0])
		rootB := find(parent, m[1])
		if rootA != rootB {
			parent[rootB] = rootA
			groups--
		}
	}
	return groups
}
