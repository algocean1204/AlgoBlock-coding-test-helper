# 틀린 까닭: 오른쪽 끝을 길이 - 1로 두어 '모든 가격보다 크다'(자리가 길이)를 돌려줄 수 없다. high가 가장 비싼 가격 이상이면 하나 덜 센다
def first_at_least(values, x):
    left = 0
    right = len(values) - 1
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
        start = first_at_least(prices, low)
        end = first_at_least(prices, high + 1)
        answer.append(end - start)
    return answer
