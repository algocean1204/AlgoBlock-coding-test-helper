package main

// 순열 도구가 없어서 재귀로 직접 만든다: 안 쓴 타일을 하나씩 뒤에 붙여 가며 모든 순서를 본다
func build(tiles string, used []bool, number int, length int, numbers map[int]bool) {
	if length >= 2 {
		numbers[number] = true // 같은 수는 맵(집합)이 한 번만 남긴다
	}
	for i := 0; i < len(tiles); i++ {
		if used[i] {
			continue
		}
		if length == 0 && tiles[i] == '0' {
			continue // 맨 앞에 0 타일은 놓을 수 없다
		}
		used[i] = true
		build(tiles, used, number*10+int(tiles[i]-'0'), length+1, numbers)
		used[i] = false
	}
}

func solution(tiles string, m int) int {
	numbers := map[int]bool{}
	build(tiles, make([]bool, len(tiles)), 0, 0, numbers)
	count := 0
	for x := range numbers {
		if x%m == 0 {
			count++
		}
	}
	return count
}
