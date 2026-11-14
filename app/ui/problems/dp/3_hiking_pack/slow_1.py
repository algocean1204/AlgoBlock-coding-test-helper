# 느린 까닭: 물건마다 넣는다/안 넣는다를 메모 없는 재귀로 모두 해 본다(물건이 100개면 2^100 갈래에 가깝다)
def solution(items, capacity):
    def best(i, left):  # i번째 물건부터 남은 무게 left로 고를 때의 최댓값
        if i == len(items):
            return 0
        weight, value = items[i]
        skip = best(i + 1, left)
        if weight <= left:
            return max(skip, best(i + 1, left - weight) + value)
        return skip

    return best(0, capacity)
