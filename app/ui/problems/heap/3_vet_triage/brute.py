def solution(patients):
    # 정렬도 힙도 쓰지 않는다: 수의사가 쉴 때마다 모든 동물을 훑어, 도착했고 아직 진료하지 않은 동물 가운데 기준대로 고른다
    n = len(patients)
    done = [False] * n
    time = 0
    total = 0
    for _ in range(n):
        best = None
        for i in range(n):
            arrive, duration, grade = patients[i]
            if done[i] or arrive > time:
                continue
            if best is None:
                best = i
                continue
            _, b_duration, b_grade = patients[best]
            if grade > b_grade or (grade == b_grade and duration < b_duration):  # 번호는 작은 것부터 보므로 같으면 앞의 것을 둔다
                best = i
        if best is None:  # 도착한 동물이 없다: 아직 진료하지 않은 동물 가운데 가장 먼저 오는 시각으로 간다
            time = min(patients[i][0] for i in range(n) if not done[i])
            for i in range(n):
                arrive, duration, grade = patients[i]
                if done[i] or arrive > time:
                    continue
                if best is None or grade > patients[best][2] or (grade == patients[best][2] and duration < patients[best][1]):
                    best = i
        done[best] = True
        total += time - patients[best][0]
        time += patients[best][1]
    return total
