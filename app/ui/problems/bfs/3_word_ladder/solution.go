package main

func solution(start string, goal string, dictionary []string) int {
	words := make(map[string]bool, len(dictionary))
	for _, w := range dictionary {
		words[w] = true
	}
	if !words[goal] {
		return -1
	}

	// steps: start에서 낱말을 만들기까지 바꾼 횟수. 들어 있으면 이미 큐에 넣은 낱말이다
	steps := map[string]int{start: 0}
	queue := []string{start} // Go에는 큐가 없어서 슬라이스와 읽는 위치(head)로 만든다
	for head := 0; head < len(queue); head++ {
		word := queue[head]
		if word == goal {
			return steps[word]
		}
		buf := []byte(word)
		for i := 0; i < len(buf); i++ {
			original := buf[i]
			for ch := byte('a'); ch <= 'z'; ch++ {
				if ch == original {
					continue
				}
				buf[i] = ch // 한 자리만 바꾼 이웃 후보를 직접 만든다
				candidate := string(buf)
				if words[candidate] {
					if _, seen := steps[candidate]; !seen {
						steps[candidate] = steps[word] + 1
						queue = append(queue, candidate)
					}
				}
			}
			buf[i] = original
		}
	}
	return -1
}
