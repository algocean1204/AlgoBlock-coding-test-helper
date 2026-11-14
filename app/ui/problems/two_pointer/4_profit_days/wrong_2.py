# 틀린 까닭: 아무 날도 더하지 않은 누적 합 0을 처음에 넣어 두지 않아, 첫째 날부터 시작하는 기간을 놓친다
def solution(profits, target):
    seen = {}
    total = 0
    count = 0
    for profit in profits:
        total += profit
        count += seen.get(total - target, 0)
        seen[total] = seen.get(total, 0) + 1
    return count
