# 느린 까닭: 손님마다 기록 전체를 다시 훑어 그 손님이 온 날을 모은다(손님 수 × 기록 수)
def solution(names, days, limit):
    steady = 0
    for name in set(names):
        mine = [days[i] for i in range(len(names)) if names[i] == name]  # 이미 날짜 순서다
        distinct = [mine[0]]
        for day in mine[1:]:
            if day != distinct[-1]:
                distinct.append(day)
        if len(distinct) >= 2 and all(distinct[k + 1] - distinct[k] <= limit for k in range(len(distinct) - 1)):
            steady += 1
    return steady
