package main

func solution(bracelets []string) int {
	count := map[string]int{} // 대표 키 → 그 디자인의 팔찌 수
	best := 0
	for _, beads := range bracelets {
		raw := []byte(beads)
		flippedBytes := make([]byte, len(raw))
		for i := range raw {
			flippedBytes[i] = raw[len(raw)-1-i]
		}
		flipped := string(flippedBytes) // 반대 방향으로 읽은 것
		key := ""
		for start := 0; start < len(beads); start++ {
			// start번째 구슬부터 같은 방향으로, 그리고 뒤집어서 읽은 모습
			same := beads[start:] + beads[:start]
			other := flipped[start:] + flipped[:start]
			if start == 0 || same < key {
				key = same
			}
			if other < key {
				key = other
			}
		}
		// 사전 순으로 가장 앞선 모습을 대표로: 디자인이 같으면 키도 같다
		count[key]++
		if count[key] > best {
			best = count[key]
		}
	}
	return best
}
