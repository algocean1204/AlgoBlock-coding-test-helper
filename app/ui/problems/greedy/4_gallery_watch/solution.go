package main

import "sort"

func solution(helpers [][]int, close int, gap int) int {
	people := append([][]int{}, helpers...)
	sort.Slice(people, func(i, j int) bool { return people[i][0] < people[j][0] }) // 오는 시각이 이른 사람부터
	reach := 0  // 시각 0부터 reach까지는 빈 시간이 모두 gap 이하다 (Go의 int는 64비트)
	best := 0   // 지금까지 본 '불러야 오는 사람' 가운데 가장 늦게 떠나는 시각
	called := 0
	i := 0
	for close-reach > gap { // 남은 시간을 비워 둘 수 없다: 누군가 더 있어야 한다
		// reach + gap 이전에 오는 사람은 지금 이어 받을 수 있다
		for i < len(people) && people[i][0] <= reach+gap {
			if people[i][2] == 1 {
				if people[i][1] > reach {
					reach = people[i][1] // 약속한 사람은 부르지 않아도 온다: 끝을 먼저 늘린다
				}
			} else if people[i][1] > best {
				best = people[i][1]
			}
			i++
		}
		if close-reach <= gap {
			break
		}
		if best <= reach {
			return -1 // 누구를 불러도 reach + gap 안에 이어 받아 더 멀리 갈 수 없다
		}
		reach = best // 이어 받을 수 있는 사람 가운데 가장 늦게 떠나는 사람을 부른다
		called++
	}
	return called
}
