# 틀린 까닭: 현재 누적 합을 딕셔너리에 먼저 넣고 찾아서, target이 0일 때 길이 0인 기간(오늘부터 오늘 전까지)까지 센다
def solution(profits, target):
    seen = {0: 1}
    total = 0
    count = 0
    for profit in profits:
        total += profit
        seen[total] = seen.get(total, 0) + 1
        count += seen.get(total - target, 0)
    return count
