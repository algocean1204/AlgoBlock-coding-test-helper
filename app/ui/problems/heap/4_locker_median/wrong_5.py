# 틀린 까닭: 모든 날을 더한 값을 32비트 int에 담는다(답이 21억을 넘어 Java·C++ 등에서 넘친다). 파이썬으로 넘침을 흉내 낸다
import heapq


def to_int32(value):
    return (value + 2**31) % 2**32 - 2**31


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
        middle = -low[0]
        total = to_int32(total + (middle * len(low) - low_sum) + (high_sum - middle * len(high)))
    return total
