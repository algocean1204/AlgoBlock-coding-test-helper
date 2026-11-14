def solution(logs, window):
    answer = []
    for time, _ in logs:
        # 정의 그대로: 시각이 time - window보다 크고 time 이하인 기록을 모두 모아 가장 큰 값
        inside = [level for t, level in logs if time - window < t <= time]
        answer.append(max(inside))
    return answer
