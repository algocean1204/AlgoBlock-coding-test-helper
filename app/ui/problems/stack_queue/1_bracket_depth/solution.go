package main

func solution(expr string) int {
	partner := map[byte]byte{')': '(', ']': '[', '}': '{'}
	stack := []byte{}
	deepest := 0
	for i := 0; i < len(expr); i++ {
		ch := expr[i]
		if ch == '(' || ch == '[' || ch == '{' {
			stack = append(stack, ch)
			if len(stack) > deepest {
				deepest = len(stack)
			}
		} else if open, ok := partner[ch]; ok {
			if len(stack) == 0 || stack[len(stack)-1] != open {
				return -1
			}
			stack = stack[:len(stack)-1]
		}
	}
	if len(stack) > 0 {
		return -1
	}
	return deepest
}
