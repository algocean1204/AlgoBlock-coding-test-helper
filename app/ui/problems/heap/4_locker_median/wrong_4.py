# 틀린 까닭: 작은 쪽 힙의 부호를 뒤집지 않아 꼭대기가 작은 쪽의 가장 큰 값이 아니라 가장 작은 값이다
import heapq


def solution(houses):
    low = []
    high = []
    low_sum = 0
    high_sum = 0
    total = 0
    for house in houses:
        if not low or house <= low[0]:
            heapq.heappush(low, house)
            low_sum += house
        else:
            heapq.heappush(high, house)
            high_sum += house
        if len(low) > len(high) + 1:
            moved = heapq.heappop(low)
            low_sum -= moved
            heapq.heappush(high, moved)
            high_sum += moved
        elif len(high) > len(low):
            moved = heapq.heappop(high)
            high_sum -= moved
            heapq.heappush(low, moved)
            low_sum += moved
        middle = low[0]
        total += (middle * len(low) - low_sum) + (high_sum - middle * len(high))
    return total
