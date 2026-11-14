# 느린 까닭: i번째 날에 공연할 때 그 앞에 공연한 날을 0 ~ i-2번째 날에서 모두 찾아본다(10만 일이면 약 50억 번)
def solution(pay):
    n = len(pay)
    take = [0] * n  # take[i]: i번째 날에 공연할 때 i번째 날까지의 최댓값
    for i in range(n):
        before = 0
        for j in range(i - 1):
            before = max(before, take[j])
        take[i] = before + pay[i]
    return max(take)
