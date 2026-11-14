def solution(prices, ranges):
    answer = []
    for low, high in ranges:
        count = 0
        for price in prices:
            if low <= price and price <= high:
                count += 1
        answer.append(count)
    return answer
