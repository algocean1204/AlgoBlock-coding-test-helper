package main

import (
	"strconv"
	"strings"
)

func solution(log []string) []int {
	count := map[string]map[string]int{} // 구역 → {종 → 마릿수}. 1마리 이상인 종만 둔다
	zonesOf := map[string]int{}          // 종 → 그 종이 1마리 이상 있는 구역 수
	answers := []int{}
	for _, line := range log {
		words := strings.Split(line, " ")
		if words[0] == "see" {
			zone, kind := words[1], words[2]
			n, _ := strconv.Atoi(words[3])
			if count[zone] == nil {
				count[zone] = map[string]int{}
			}
			inZone := count[zone]
			before := inZone[kind] // 덮어쓰기 전에 지금 값을 본다(없으면 0)
			// 종의 구역 수는 없음 → 있음, 있음 → 없음으로 바뀔 때만 달라진다
			if before == 0 && n > 0 {
				zonesOf[kind]++
			}
			if before > 0 && n == 0 {
				zonesOf[kind]--
			}
			if n > 0 {
				inZone[kind] = n // 더하지 않고 바꾼다
			} else {
				delete(inZone, kind) // 0마리는 지운다: 구역의 종 수 = 안쪽 표의 크기
			}
		} else if words[0] == "zone" {
			answers = append(answers, len(count[words[1]]))
		} else {
			answers = append(answers, zonesOf[words[1]])
		}
	}
	return answers
}
