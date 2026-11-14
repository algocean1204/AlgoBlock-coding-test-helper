package main

func solution(n int, chargers []int) int64 {
	fastest := chargers[0]
	for _, minute := range chargers {
		if minute < fastest {
			fastest = minute
		}
	}
	// Go의 int는 64비트라 5 x 10^13도 담긴다. 반환만 int64로 바꾼다
	left := 1
	right := fastest * n
	for left < right {
		mid := (left + right) / 2
		done := 0
		for _, minute := range chargers {
			done += mid / minute
		}
		if done >= n {
			right = mid
		} else {
			left = mid + 1
		}
	}
	return int64(left)
}
