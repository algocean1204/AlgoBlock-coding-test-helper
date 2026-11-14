# 틀린 까닭: 보관함을 평균 위치(소수점 아래 버림)에 둔다(거리 합은 가운데 값에서 가장 작다)
def solution(houses):
    total = 0
    position_sum = 0
    for day, house in enumerate(houses, 1):
        position_sum += house
        spot = position_sum // day
        total += sum(abs(h - spot) for h in houses[:day])
    return total
