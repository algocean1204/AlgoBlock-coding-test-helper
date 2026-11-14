# 틀린 까닭: 두 경계를 모두 'x보다 큰 값이 처음 나오는 자리'로 구해, 가격이 low와 같은 매물을 빼먹는다
def first_greater(values, x):
    left = 0
    right = len(values)
    while left < right:
        mid = (left + right) // 2
        if values[mid] > x:
            right = mid
        else:
            left = mid + 1
    return left


def solution(prices, ranges):
    prices = sorted(prices)
    answer = []
    for low, high in ranges:
        answer.append(first_greater(prices, high) - first_greater(prices, low))
    return answer
