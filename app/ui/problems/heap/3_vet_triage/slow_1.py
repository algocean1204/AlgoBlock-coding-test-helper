# 느린 까닭: 고를 때마다 기다리는 동물을 모두 훑어 가장 위급한 것을 찾는다(한꺼번에 몰려오면 n × n에 가깝다)
def solution(patients):
    n = len(patients)
    arrivals = sorted((arrive, duration, grade, i) for i, (arrive, duration, grade) in enumerate(patients))
    waiting = []
    time = 0
    next_arrival = 0
    total = 0
    for _ in range(n):
        if not waiting and arrivals[next_arrival][0] > time:
            time = arrivals[next_arrival][0]
        while next_arrival < n and arrivals[next_arrival][0] <= time:
            arrive, duration, grade, i = arrivals[next_arrival]
            waiting.append((-grade, duration, i, arrive))
            next_arrival += 1
        best = min(waiting)
        waiting.remove(best)
        total += time - best[3]
        time += best[1]
    return total
