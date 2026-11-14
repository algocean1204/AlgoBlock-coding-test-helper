package main

// day일까지(그날 포함) 이루어진 점검 수. 모두 400억 번까지라 int64로 센다
func countUntil(schedules [][]int, day int64) int64 {
	var total int64
	for _, s := range schedules {
		first, gap, times := int64(s[0]), int64(s[1]), int64(s[2])
		if day >= first { // 첫 점검 전이면 0번
			count := (day-first)/gap + 1
			if count > times { // times번을 넘지 않는다
				count = times
			}
			total += count
		}
	}
	return total
}

func solution(schedules [][]int, k int64) int64 {
	left, right := int64(schedules[0][0]), int64(0)
	for _, s := range schedules {
		first, gap, times := int64(s[0]), int64(s[1]), int64(s[2])
		if first < left {
			left = first
		}
		if last := first + (times-1)*gap; last > right {
			right = last
		}
	}
	// 그날까지의 점검이 k번 이상인 가장 이른 날을 찾는다
	for left < right {
		mid := (left + right) / 2
		if countUntil(schedules, mid) >= k {
			right = mid
		} else {
			left = mid + 1
		}
	}
	return left
}
