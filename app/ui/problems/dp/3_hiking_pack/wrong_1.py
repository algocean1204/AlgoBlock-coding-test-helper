# 틀린 까닭: 무게당 쓸모가 큰 물건부터 들어가는 대로 넣는다(물건을 쪼갤 수 없으면 탐욕이 틀린다)
def solution(items, capacity):
    order = sorted(items, key=lambda item: item[1] / item[0], reverse=True)
    left = capacity
    total = 0
    for weight, value in order:
        if weight <= left:
            left -= weight
            total += value
    return total
