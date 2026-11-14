package main

import (
	"sort"
	"strconv"
	"strings"
)

// 할증 시간: 07:30 이상 09:30 미만, 17:00 이상 19:00 미만(분)
var rush = [][2]int{{7*60 + 30, 9*60 + 30}, {17 * 60, 19 * 60}}

func toMinutes(clock string) int {
	hour, _ := strconv.Atoi(clock[:2])
	minute, _ := strconv.Atoi(clock[3:])
	return hour*60 + minute
}

func rideFee(start, end, perMinute int) int {
	// 탄 분마다 1분 요금, 할증 시간과 겹친 분은 1분 요금을 한 번 더
	fee := (end - start) * perMinute
	for _, r := range rush {
		overlap := min(end, r[1]) - max(start, r[0])
		if overlap > 0 {
			fee += overlap * perMinute
		}
	}
	return fee
}

func solution(rides []string, price []int, gap int) [][]int {
	unlock, perMinute, dayMax := price[0], price[1], price[2]

	total := map[string]int{}   // 회원 → 그날 요금 합
	lastEnd := map[string]int{} // 회원 → 바로 앞 기록의 끝 시각(분)
	for _, ride := range rides {
		words := strings.Split(ride, " ")
		member := words[0]
		start := toMinutes(words[1])
		end := toMinutes(words[2])
		fee := rideFee(start, end, perMinute)
		// 같은 회원의 바로 앞 기록이 끝난 지 gap분 이하이면 이어 탄 것: 잠금 해제 요금이 없다
		previous, seen := lastEnd[member]
		if !seen || start-previous > gap {
			fee += unlock
		}
		total[member] += fee
		lastEnd[member] = end
	}

	answer := [][]int{}
	for member, sum := range total {
		number, _ := strconv.Atoi(member)
		answer = append(answer, []int{number, min(sum, dayMax)}) // 상한은 하루 합에 한 번
	}
	// 요금이 많은 회원부터, 같으면 번호가 작은 회원부터
	sort.Slice(answer, func(i, j int) bool {
		if answer[i][1] != answer[j][1] {
			return answer[i][1] > answer[j][1]
		}
		return answer[i][0] < answer[j][0]
	})
	return answer
}
