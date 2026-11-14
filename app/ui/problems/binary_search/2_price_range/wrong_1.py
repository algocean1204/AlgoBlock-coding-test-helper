# 틀린 까닭: 두 경계를 모두 'x 이상이 처음 나오는 자리'로 구해, 가격이 high와 같은 매물을 빼먹는다
def first_at_least(values, x):
    left = 0
    right = len(values)
    while left < right:
        mid = (left + right) // 2
        if values[mid] >= x:
            right = mid
        else:
            left = mid + 1
    return left


def solution(prices, ranges):
    prices = sorted(prices)
    answer = []
    for low, high in ranges:
        answer.append(first_at_least(prices, high) - first_at_least(prices, low))
    return answer
