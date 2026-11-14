package main

func solution(books []int, queries []int) []int {
	answer := []int{}
	for _, target := range queries {
		left := 0
		right := len(books) - 1
		position := -1
		for left <= right {
			mid := (left + right) / 2
			if books[mid] == target {
				position = mid
				break
			} else if books[mid] < target {
				left = mid + 1
			} else {
				right = mid - 1
			}
		}
		answer = append(answer, position)
	}
	return answer
}
