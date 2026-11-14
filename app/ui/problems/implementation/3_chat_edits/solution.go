package main

import "strings"

func solution(records []string) []string {
	// 첫 번째 훑기: 메시지마다 마지막 상태(보낸이, 마지막 내용, 고친 적 있는가, 지워졌는가)를 모은다
	order := []string{}
	sender := map[string]string{}
	text := map[string]string{}
	edited := map[string]bool{}
	deleted := map[string]bool{}
	for _, record := range records {
		words := strings.Split(record, " ")
		number := words[1]
		if words[0] == "SEND" {
			order = append(order, number)
			sender[number] = words[2]
			text[number] = words[3]
		} else if words[0] == "EDIT" {
			text[number] = words[2]
			edited[number] = true
		} else {
			deleted[number] = true
		}
	}

	// 두 번째 훑기: 남은 메시지를 보낸 순서대로 보며, 바로 앞 줄과 보낸이가 같으면 그 줄에 붙인다
	lines := []*strings.Builder{}
	lineSender := ""
	for _, number := range order {
		if deleted[number] {
			continue
		}
		shown := text[number]
		if edited[number] {
			shown += "*"
		}
		if len(lines) > 0 && lineSender == sender[number] {
			lines[len(lines)-1].WriteString(" " + shown)
		} else {
			line := &strings.Builder{}
			line.WriteString(sender[number] + ": " + shown)
			lines = append(lines, line)
			lineSender = sender[number]
		}
	}
	answer := make([]string, len(lines))
	for i, line := range lines {
		answer[i] = line.String()
	}
	return answer
}
