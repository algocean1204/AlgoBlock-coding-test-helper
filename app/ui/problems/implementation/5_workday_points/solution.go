package main

import (
	"sort"
	"strconv"
)

var monthDays = []int{31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31}

func isLeap(year int) bool {
	if year%400 == 0 {
		return true
	}
	if year%100 == 0 {
		return false
	}
	return year%4 == 0
}

func solution(staff [][]string, today string) []int64 {
	// 해마다 '1년 1월 1일부터 그해 1월 1일까지 며칠인가'를 한 번만 구해 둔다
	yearStart := make([]int64, 10000)
	var days int64 = 0
	for year := 1; year < 10000; year++ {
		yearStart[year] = days
		if isLeap(year) {
			days += 366
		} else {
			days += 365
		}
	}

	dayNumber := func(date string) int64 {
		// "YYYY-MM-DD" → 1년 1월 1일이 0, 그다음 날이 1, …
		year, _ := strconv.Atoi(date[0:4])
		month, _ := strconv.Atoi(date[5:7])
		day, _ := strconv.Atoi(date[8:10])
		number := yearStart[year]
		for m := 1; m < month; m++ { // 그해에 지나간 달의 날 수
			number += int64(monthDays[m-1])
			if m == 2 && isLeap(year) {
				number++
			}
		}
		return number + int64(day) - 1
	}

	weekdays := func(first, last int64) int64 {
		// first일째부터 last일째까지(둘 다 셈) 평일 수. 0일째가 월요일이므로 (일 번호 % 7) < 5이면 평일
		total := last - first + 1
		weeks := total / 7
		count := weeks * 5                                 // 7일 묶음마다 평일 5일. 점수 합이 약 1,300억이라 int64
		for number := first + weeks*7; number <= last; number++ { // 남은 6일 이하는 하나씩 본다
			if number%7 < 5 {
				count++
			}
		}
		return count
	}

	todayNumber := dayNumber(today)
	points := map[string]int64{}
	for _, row := range staff {
		last := todayNumber
		if row[2] != "-" {
			last = dayNumber(row[2])
		}
		points[row[0]] += weekdays(dayNumber(row[1]), last)
	}

	// Go의 map은 순서가 없다. 부서 이름을 모아 사전 순으로 정렬한다
	teams := []string{}
	for team := range points {
		teams = append(teams, team)
	}
	sort.Strings(teams)

	answer := []int64{}
	for _, team := range teams {
		answer = append(answer, points[team])
	}
	return answer
}
