package main

import "sort"

func solution(kinds []string, minutes []int, time int) int {
	// 모양마다 그 도장을 받는 가장 짧은 시간만 남긴다(같은 모양은 한 칸만 채우므로)
	shortest := map[string]int{}
	for i, kind := range kinds {
		before, ok := shortest[kind]
		if !ok || minutes[i] < before {
			shortest[kind] = minutes[i]
		}
	}
	sorted := []int{}
	for _, minute := range shortest {
		sorted = append(sorted, minute)
	}
	sort.Ints(sorted) // 짧은 것부터

	used := 0   // 지금까지 쓴 시간 (Go의 int는 64비트)
	filled := 0 // 채운 칸 수
	for _, minute := range sorted {
		if used+minute > time {
			break // 이것이 안 들어가면 뒤의 더 긴 것도 안 들어간다
		}
		used += minute
		filled++
	}
	return filled
}
