# 틀린 까닭: 새 값을 꼭대기와 비교하지 않고 개수만 보고 두 힙에 번갈아 넣는다(작은 쪽과 큰 쪽이 섞인다)
import heapq


def solution(houses):
    low = []
    high = []
    low_sum = 0
    high_sum = 0
    total = 0
    for house in houses:
        if len(low) == len(high):
            heapq.heappush(low, -house)
            low_sum += house
        else:
            heapq.heappush(high, house)
            high_sum += house
        middle = -low[0]
        total += (middle * len(low) - low_sum) + (high_sum - middle * len(high))
    return total
