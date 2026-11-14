package main

func solution(members int, roles int, auditions [][]int, rivals [][]int) int {
	n := members // 단원 수
	// scores[단원][배역] = 오디션 점수. 0은 오디션을 보지 않아 맡을 수 없다는 뜻
	scores := make([][]int, n)
	for i := range scores {
		scores[i] = make([]int, roles)
	}
	for _, a := range auditions {
		scores[a[0]][a[1]] = a[2]
	}
	rivalMask := make([]int, n) // 함께 무대에 설 수 없는 단원들(비트, 양쪽에 모두 적는다)
	for _, pair := range rivals {
		rivalMask[pair[0]] |= 1 << pair[1]
		rivalMask[pair[1]] |= 1 << pair[0]
	}
	// memo[몇 번 배역부터][누구를 썼는가(비트)] = 거기서 더 얻을 수 있는 가장 큰 점수. -2는 아직 모름
	memo := make([][]int, roles)
	for i := range memo {
		memo[i] = make([]int, 1<<n)
		for j := range memo[i] {
			memo[i][j] = -2
		}
	}

	// index번 배역부터 끝까지 정해서 더 얻을 수 있는 가장 큰 점수. 끝까지 정할 수 없으면 -1
	var best func(index, used int) int
	best = func(index, used int) int {
		if index == roles {
			return 0
		}
		if memo[index][used] != -2 { // 같은 상태에 다시 왔다: 기억한 값을 쓴다
			return memo[index][used]
		}
		result := -1
		for person := 0; person < n; person++ {
			if used>>person&1 == 1 || scores[person][index] == 0 {
				continue
			}
			if used&rivalMask[person] != 0 { // 이미 정한 단원과 부딪치면 이 가지는 버린다
				continue
			}
			rest := best(index+1, used|1<<person)
			if rest != -1 && scores[person][index]+rest > result { // 뒤의 배역을 끝까지 정할 수 있을 때만 후보가 된다
				result = scores[person][index] + rest
			}
		}
		memo[index][used] = result
		return result
	}

	return best(0, 0)
}
