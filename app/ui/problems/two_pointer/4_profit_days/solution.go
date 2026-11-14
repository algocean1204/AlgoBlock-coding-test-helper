package main

func solution(profits []int, target int) int64 {
	// seen[s]: 지금까지 나온 누적 합 가운데 값이 s인 것의 개수
	// 아무 날도 더하지 않은 누적 합 0을 한 번 넣어 두어야 첫째 날부터 시작하는 기간도 센다
	seen := map[int]int{0: 1}
	total := 0
	// 개수가 최대 약 50억이라 int32면 넘치지만, Go의 int는 64비트이고 반환형은 int64다
	count := int64(0)
	for _, profit := range profits {
		total += profit
		// 앞쪽 누적 합이 total - target이었다면, 그다음 날부터 오늘까지의 합이 target이다
		// Go의 map은 없는 키를 읽으면 0을 돌려준다
		count += int64(seen[total-target])
		seen[total]++
	}
	return count
}
