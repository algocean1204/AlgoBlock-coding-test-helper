# 느린 까닭: 매초 지금까지 출발한 사람을 모두 다시 훑어 미끄럼틀 안에 있는 사람을 센다(걸린 시간 × 출발한 사람 수만큼 센다)
def solution(arrive, ride, gap, cap):
    starts = []
    total = 0
    time = 0
    while len(starts) < len(arrive):
        i = len(starts)
        inside = 0
        for s in starts:
            if s + ride > time:
                inside += 1
        if arrive[i] <= time and inside < cap and (not starts or time - starts[-1] >= gap):
            starts.append(time)
            total += time - arrive[i]
        time += 1
    return total
