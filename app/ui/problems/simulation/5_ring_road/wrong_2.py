# 틀린 까닭: 주기가 0초부터 시작한다고 보고 t를 주기로 나눈 나머지로 계산한다(처음 몇 초의 모습은 다시 나오지 않을 수 있다)
def solution(road, t):
    n = len(road)
    first_seen = {}  # 도로 모습 → 그 모습이 처음 나온 시각(초)
    passed = [0]     # passed[s] = 처음 s초 동안 결승선을 지나간 횟수
    state = road
    second = 0
    while second < t and state not in first_seen:
        first_seen[state] = second
        crossed = 1 if state[n - 1] == '>' and state[0] == '.' else 0
        # 1초가 시작될 때의 state만 보고 새 도로 new_road에 적는다
        new_road = ['.'] * n
        for i in range(n):
            if state[i] == '>':
                front = (i + 1) % n
                if state[front] == '.':
                    new_road[front] = '>'
                else:
                    new_road[i] = '>'
        state = ''.join(new_road)
        second += 1
        passed.append(passed[-1] + crossed)
    if second == t:
        return passed[t]
    # second초의 모습이 start초에 이미 나왔다: start초부터 cycle초마다 같은 흐름이 되풀이된다
    start = first_seen[state]
    cycle = second - start
    per_cycle = passed[second] - passed[start]
    full, rest = divmod(t, cycle)
    return full * per_cycle + passed[rest]
