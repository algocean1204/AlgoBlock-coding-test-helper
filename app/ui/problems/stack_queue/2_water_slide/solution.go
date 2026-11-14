package main

func solution(arrive []int, ride int, gap int, cap int) int {
	// 미끄럼틀 안에 있는 사람이 벗어나는 시각. 먼저 출발한 사람이 앞.
	// 맨 앞 자리(head)를 따로 들고 다니며 큐처럼 쓴다
	sliding := []int{}
	head := 0
	nextPerson := 0 // 줄의 맨 앞 사람 번호
	lastStart := -1 // 바로 앞사람이 출발한 시각(아직 아무도 출발하지 않았으면 -1)
	total := 0
	time := 0
	for nextPerson < len(arrive) {
		for head < len(sliding) && sliding[head] == time { // 먼저 벗어난다
			head++
		}
		arrived := arrive[nextPerson] <= time
		room := len(sliding)-head < cap
		gapPassed := lastStart == -1 || time-lastStart >= gap
		if arrived && room && gapPassed { // 그다음 맨 앞 사람 한 명이 출발한다
			sliding = append(sliding, time+ride)
			total += time - arrive[nextPerson]
			lastStart = time
			nextPerson++
		}
		time++
	}
	return total
}
