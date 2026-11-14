package main

func solution(road string, t int64) int64 {
	n := len(road)
	firstSeen := map[string]int{} // 도로 모습 → 그 모습이 처음 나온 시각(초)
	passed := []int64{0}          // passed[s] = 처음 s초 동안 결승선을 지나간 횟수
	state := road
	second := 0
	for int64(second) < t {
		if _, seen := firstSeen[state]; seen {
			break
		}
		firstSeen[state] = second
		var crossed int64 = 0
		if state[n-1] == '>' && state[0] == '.' {
			crossed = 1
		}
		// 1초가 시작될 때의 state만 보고 새 도로 newRoad에 적는다
		newRoad := make([]byte, n)
		for i := range newRoad {
			newRoad[i] = '.'
		}
		for i := 0; i < n; i++ {
			if state[i] == '>' {
				front := (i + 1) % n
				if state[front] == '.' {
					newRoad[front] = '>'
				} else {
					newRoad[i] = '>'
				}
			}
		}
		state = string(newRoad)
		second++
		passed = append(passed, passed[len(passed)-1]+crossed)
	}
	if int64(second) == t {
		return passed[t]
	}
	// second초의 모습이 start초에 이미 나왔다: start초부터 cycle초마다 같은 흐름이 되풀이된다
	start := firstSeen[state]
	cycle := int64(second - start)
	perCycle := passed[second] - passed[start]
	full := (t - int64(start)) / cycle
	rest := int((t - int64(start)) % cycle)
	return passed[start] + full*perCycle + (passed[start+rest] - passed[start])
}
