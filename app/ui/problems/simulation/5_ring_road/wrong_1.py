# 틀린 까닭: 자동차를 0번부터 차례로 제자리에서 옮겨, 방금 옮긴 자동차를 다음 칸에서 또 옮긴다(1초에 여러 칸을 간다)
def solution(road, t):
    n = len(road)
    first_seen = {}  # 도로 모습 → 그 모습이 처음 나온 시각(초)
    passed = [0]     # passed[s] = 처음 s초 동안 결승선을 지나간 횟수
    state = road
    second = 0
    while second < t and state not in first_seen:
        first_seen[state] = second
        crossed = 0
        cells = list(state)
        for i in range(n):
            if cells[i] == '>':
                front = (i + 1) % n
                if cells[front] == '.':
                    cells[i], cells[front] = '.', '>'
                    if i == n - 1:
                        crossed = 1
        state = ''.join(cells)
        second += 1
        passed.append(passed[-1] + crossed)
    if second == t:
        return passed[t]
    # second초의 모습이 start초에 이미 나왔다: start초부터 cycle초마다 같은 흐름이 되풀이된다
    start = first_seen[state]
    cycle = second - start
    per_cycle = passed[second] - passed[start]
    full, rest = divmod(t - start, cycle)
    return passed[start] + full * per_cycle + (passed[start + rest] - passed[start])
