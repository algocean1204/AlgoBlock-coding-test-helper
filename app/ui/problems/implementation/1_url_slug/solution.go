package main

import (
	"strconv"
	"strings"
)

func solution(title string, taken []string) string {
	skip := map[string]bool{"a": true, "an": true, "the": true, "of": true, "and": true}

	// 1~2. 빈칸으로 나누고(Fields는 빈 낱말을 만들지 않는다), 낱말마다 소문자로 바꿔 영문 소문자·숫자만 남긴다
	words := []string{}
	for _, word := range strings.Fields(title) {
		kept := ""
		for _, ch := range strings.ToLower(word) {
			if (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9') {
				kept += string(ch)
			}
		}
		if kept != "" {
			words = append(words, kept)
		}
	}

	// 3. 규칙 3의 낱말 빼기. 다 빠져 목록이 비면 빼지 않는다
	left := []string{}
	for _, word := range words {
		if !skip[word] {
			left = append(left, word)
		}
	}
	if len(left) > 0 {
		words = left
	}

	// 4. 낱말 단위로 이어 붙이다가 길이가 24를 넘게 되면 멈춘다
	slug := words[0]
	if len(slug) > 24 {
		slug = slug[:24]
	}
	for _, word := range words[1:] {
		if len(slug)+1+len(word) > 24 {
			break
		}
		slug = slug + "-" + word
	}

	// 5. taken에 있으면 -2, -3, … 을 붙여 본다
	used := map[string]bool{}
	for _, name := range taken {
		used[name] = true
	}
	if !used[slug] {
		return slug
	}
	number := 2
	for used[slug+"-"+strconv.Itoa(number)] {
		number++
	}
	return slug + "-" + strconv.Itoa(number)
}
