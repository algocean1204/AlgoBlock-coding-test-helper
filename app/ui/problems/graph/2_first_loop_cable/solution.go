package main

// 재귀 대신 반복문: 긴 줄 입력에서 깊어지지 않게
func find(parent map[string]string, x string) string {
	if _, ok := parent[x]; !ok {
		parent[x] = x
	}
	for parent[x] != x {
		parent[x] = parent[parent[x]] // 경로 압축
		x = parent[x]
	}
	return x
}

func solution(cables [][]string) int {
	parent := map[string]string{} // 정점이 이름(문자열)이라 맵을 쓴다

	for i, c := range cables {
		rootX := find(parent, c[0])
		rootY := find(parent, c[1])
		if rootX == rootY {
			return i + 1 // 몇 번째 케이블인지는 1부터 센다
		}
		parent[rootY] = rootX
	}
	return -1
}
