# 느린 까닭: 검색마다 매물을 모두 훑어 센다(검색 5만 번 × 매물 10만 개)
def solution(prices, ranges):
    return [sum(1 for price in prices if low <= price <= high) for low, high in ranges]
