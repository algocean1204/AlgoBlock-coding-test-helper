package main

// remaining: 더 놓아야 할 자리 수, last: 바로 앞에 놓은 장르 번호(처음에는 -1)
func place(remaining int, last int, left []int) int {
	if remaining == 0 {
		return 1
	}
	ways := 0
	for genre := 0; genre < len(left); genre++ {
		if left[genre] == 0 || genre == last { // 놓는 도중에 가지를 끊는다
			continue
		}
		left[genre]--
		ways += place(remaining-1, genre, left)
		left[genre]++
	}
	return ways
}

func solution(genres []string) int {
	// 같은 장르를 개수로 묶는다: left[장르 번호] = 아직 안 놓은 팀 수
	number := map[string]int{}
	left := []int{}
	for _, genre := range genres {
		at, ok := number[genre]
		if !ok {
			at = len(left)
			number[genre] = at
			left = append(left, 0)
		}
		left[at]++
	}
	return place(len(genres), -1, left)
}
