package main

func solution(names []string, days []int, limit int) int {
	last := map[string]int{}     // 손님 → 마지막으로 온 날
	visits := map[string]int{}   // 손님 → 서로 다른 날에 온 횟수
	broken := map[string]bool{}  // 이웃한 두 날의 차이가 limit을 넘은 적이 있는 손님
	for i, name := range names {
		day := days[i]
		before, ok := last[name]
		if !ok { // 처음 온 손님
			last[name] = day
			visits[name] = 1
		} else if day != before { // 같은 날 다시 들어온 것은 새 방문이 아니다
			if day-before > limit {
				broken[name] = true
			}
			last[name] = day // 이제 이 날이 마지막으로 온 날이다
			visits[name]++
		}
	}

	steady := 0
	for name, count := range visits {
		if count >= 2 && !broken[name] {
			steady++
		}
	}
	return steady
}
