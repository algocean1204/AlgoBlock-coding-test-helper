# 느린 까닭: 1초씩 t초를 끝까지 돌린다(t가 1조이면 1조 번 × 도로 길이)
def solution(road, t):
    n = len(road)
    state = road
    total = 0
    for _ in range(t):
        if state[n - 1] == '>' and state[0] == '.':
            total += 1
        new_road = ['.'] * n
        for i in range(n):
            if state[i] == '>':
                front = (i + 1) % n
                if state[front] == '.':
                    new_road[front] = '>'
                else:
                    new_road[i] = '>'
        state = ''.join(new_road)
    return total
