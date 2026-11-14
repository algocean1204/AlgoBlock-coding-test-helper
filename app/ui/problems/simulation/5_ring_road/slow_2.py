# 느린 까닭: 4단계처럼 도로가 바뀌지 않을 때만 멈춘다(자동차가 계속 도는 도로는 끝까지 바뀌므로 t초를 다 돌린다)
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
        new_state = ''.join(new_road)
        if new_state == state:
            break
        state = new_state
    return total
