# 느린 까닭: 날마다 지금까지의 위치를 정렬해 가운데 값을 찾고 거리를 모두 다시 더한다(10만 일이면 10만 × 10만 번을 넘는다)
def solution(houses):
    total = 0
    for day in range(1, len(houses) + 1):
        built = sorted(houses[:day])
        middle = built[(day - 1) // 2]
        total += sum(abs(house - middle) for house in built)
    return total
