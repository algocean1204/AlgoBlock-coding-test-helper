# 틀린 까닭: 거리 합을 '큰 쪽 합 - 작은 쪽 합'으로만 구해, 개수가 홀수일 때 가운데 값의 몫을 빠뜨린다
import heapq


def solution(houses):
    low = []
    high = []
    low_sum = 0
    high_sum = 0
    total = 0
    for house in houses:
        if not low or house <= -low[0]:
            heapq.heappush(low, -house)
            low_sum += house
        else:
            heapq.heappush(high, house)
            high_sum += house
        if len(low) > len(high) + 1:
            moved = -heapq.heappop(low)
            low_sum -= moved
            heapq.heappush(high, moved)
            high_sum += moved
        elif len(high) > len(low):
            moved = heapq.heappop(high)
            high_sum -= moved
            heapq.heappush(low, -moved)
            low_sum += moved
        total += high_sum - low_sum
    return total
