# 틀린 까닭: prices를 정렬하지 않은 채 이분탐색한다(가운데 값만 보고 절반을 버릴 수 없다)
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
    answer = []
    for low, high in ranges:
        start = first_at_least(prices, low)
        end = first_at_least(prices, high + 1)
        answer.append(end - start)
    return answer
