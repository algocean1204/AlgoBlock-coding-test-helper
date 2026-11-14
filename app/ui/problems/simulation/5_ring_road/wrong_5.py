# 틀린 까닭: 지나간 횟수를 32비트 int에 담아 넘친다(Java·C++에서 int로 계산한 것과 같다. 1조 초면 21억을 넘을 수 있다)
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
    full, rest = divmod(t - start, cycle)
    answer = passed[start] + full * per_cycle + (passed[start + rest] - passed[start])
    return (answer + 2**31) % 2**32 - 2**31  # int에 담으면 넘쳐서 이렇게 된다
