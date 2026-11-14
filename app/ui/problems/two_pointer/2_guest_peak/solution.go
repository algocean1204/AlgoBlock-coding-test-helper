package main

func solution(days int, bookings [][]int) int {
	// diff[d]: d일에 새로 늘어나는(음수면 줄어드는) 손님 수. last + 1일 = days + 1일까지 쓰므로 days + 2칸
	diff := make([]int, days+2)
	for _, booking := range bookings {
		first, last, guests := booking[0], booking[1], booking[2]
		diff[first] += guests
		diff[last+1] -= guests
	}
	// 1일부터 누적하면 그날 묵는 사람 수가 된다
	best := 0
	staying := 0
	for day := 1; day <= days; day++ {
		staying += diff[day]
		if staying > best {
			best = staying
		}
	}
	return best
}
