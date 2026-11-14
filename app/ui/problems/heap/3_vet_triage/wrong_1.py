# 틀린 까닭: 도착한 순서대로만 진료한다(위급도가 큰 동물을 먼저 골라야 한다)
def solution(patients):
    arrivals = sorted((arrive, i, duration) for i, (arrive, duration, grade) in enumerate(patients))
    time = 0
    total = 0
    for arrive, i, duration in arrivals:
        time = max(time, arrive)
        total += time - arrive
        time += duration
    return total
