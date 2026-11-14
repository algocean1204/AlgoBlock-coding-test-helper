# 틀린 까닭: 힙의 길이(len)로 판자 수를 센다(지울 표시만 하고 아직 힙에 남은 판자까지 세어 균형과 비용이 어긋난다)
import heapq


def drop_old(heap, left):
    while heap and heap[0][1] < left:
        heapq.heappop(heap)


def solution(heights, w):
    low = []
    high = []
    in_low = [False] * len(heights)
    low_sum = high_sum = 0
    left = 0
    costs = []
    for right, height in enumerate(heights):
        drop_old(low, left)
        if not low or height <= -low[0][0]:
            heapq.heappush(low, (-height, right))
            in_low[right] = True
            low_sum += height
        else:
            heapq.heappush(high, (height, right))
            high_sum += height
        if right - left + 1 > w:
            if in_low[left]:
                low_sum -= heights[left]
            else:
                high_sum -= heights[left]
            left += 1
        drop_old(low, left)
        drop_old(high, left)
        while len(low) > len(high) + 1:
            minus_height, index = heapq.heappop(low)
            moved = -minus_height
            heapq.heappush(high, (moved, index))
            in_low[index] = False
            low_sum -= moved
            high_sum += moved
            drop_old(low, left)
        while len(high) > len(low):
            moved, index = heapq.heappop(high)
            heapq.heappush(low, (-moved, index))
            in_low[index] = True
            high_sum -= moved
            low_sum += moved
            drop_old(high, left)
        if right - left + 1 == w:
            middle = -low[0][0]
            costs.append((middle * len(low) - low_sum) + (high_sum - middle * len(high)))
    return costs
