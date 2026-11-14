package main

func solution(loans []string, k int) []string {
	count := map[string]int{} // 제목마다 지금까지 빌려진 횟수 (없는 키는 0으로 읽힌다)
	shelf := []string{}       // 추천 서가에 꽂힌 차례대로
	for _, title := range loans {
		count[title]++
		if count[title] == k { // 바로 지금 k번째로 빌려졌다
			shelf = append(shelf, title)
		}
	}
	return shelf
}
