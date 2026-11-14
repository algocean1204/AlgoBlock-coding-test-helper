package main

import "strings"

func solution(base int, reading int64) []int64 {
	const digits = "0123456789ABCDEF"
	b := int64(base)

	// 나머지를 끝 자리부터 모은 뒤 뒤집는다
	reversed := []byte{}
	for reading > 0 {
		reversed = append(reversed, digits[reading%b])
		reading /= b
	}
	text := make([]byte, len(reversed))
	for i := range reversed {
		text[i] = reversed[len(reversed)-1-i]
	}

	// 앞 자리보다 작아지는 곳에서 새 조각을 시작한다
	pieces := []string{string(text[0])}
	for i := 1; i < len(text); i++ {
		if strings.IndexByte(digits, text[i]) < strings.IndexByte(digits, text[i-1]) {
			pieces = append(pieces, string(text[i]))
		} else {
			pieces[len(pieces)-1] += string(text[i])
		}
	}

	// 조각마다 앞자리부터 값 = 값 × base + 자리값으로 읽어 가장 큰 값을 고른다
	var largest int64 = 0
	for _, piece := range pieces {
		var value int64 = 0
		for i := 0; i < len(piece); i++ {
			value = value*b + int64(strings.IndexByte(digits, piece[i]))
		}
		if value > largest {
			largest = value
		}
	}
	return []int64{int64(len(pieces)), largest}
}
