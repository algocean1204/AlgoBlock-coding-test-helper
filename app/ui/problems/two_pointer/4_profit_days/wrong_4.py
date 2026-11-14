# 틀린 까닭: 누적 합이 나왔는지만 집합으로 기억해, 같은 누적 합이 여러 번 나온 것을 한 번으로 센다
def solution(profits, target):
    seen = {0}
    total = 0
    count = 0
    for profit in profits:
        total += profit
        if total - target in seen:
            count += 1
        seen.add(total)
    return count
