def solution(schedules, k):
    # 글의 정의를 그대로: 모든 점검일을 만들어 이른 순으로 늘어놓는다
    days = []
    for first, gap, times in schedules:
        for t in range(times):
            days.append(first + t * gap)
    days.sort()
    return days[k - 1]
