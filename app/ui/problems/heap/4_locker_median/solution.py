import heapq


def solution(houses):
    low = []   # 작은 쪽 절반. 부호를 뒤집어 넣어 가장 큰 값이 꼭대기에 온다
    high = []  # 큰 쪽 절반. 가장 작은 값이 꼭대기에 온다
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
        # 개수 맞추기: low가 high와 같거나 하나 더 많게 둔다. 그러면 low의 꼭대기가 가운데 값이다
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
        # (작은 쪽 집들에서 가운데까지의 거리 합) + (큰 쪽 집들에서 가운데까지의 거리 합)
        total += (middle * len(low) - low_sum) + (high_sum - middle * len(high))
    return total
