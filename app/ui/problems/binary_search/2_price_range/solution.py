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
        start = first_at_least(prices, low)
        # 가격이 정수라서 'high보다 큰 값이 처음 나오는 자리' = 'high + 1 이상이 처음 나오는 자리'
        end = first_at_least(prices, high + 1)
        answer.append(end - start)
    return answer
