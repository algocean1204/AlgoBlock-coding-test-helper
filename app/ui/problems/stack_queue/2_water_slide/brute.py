def solution(arrive, ride, gap, cap):
    # 사람마다 출발 시각을 정의대로 하나씩 정한다
    start = []
    for i in range(len(arrive)):
        t = arrive[i] if i == 0 else max(arrive[i], start[i - 1] + gap)
        while True:
            # t초에 벗어날 사람이 벗어난 뒤 미끄럼틀 안에 남은 사람: 앞서 출발한 사람 가운데 벗어나는 시각이 t보다 늦은 사람
            inside = sum(1 for j in range(i) if start[j] + ride > t)
            if inside < cap:
                break
            t += 1
        start.append(t)
    return sum(start[i] - arrive[i] for i in range(len(arrive)))
