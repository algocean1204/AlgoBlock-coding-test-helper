# 틀린 까닭: 빠지는 판자가 어느 힙에 있는지 높이만 보고 짐작한다(같은 높이가 두 힙에 나뉘어 있으면 엉뚱한 쪽의 개수와 합을 줄인다)
import heapq


def drop_old(heap, left):
    while heap and heap[0][1] < left:
        heapq.heappop(heap)


def solution(heights, w):
    low = []
    high = []
    low_count = high_count = 0
    low_sum = high_sum = 0
    left = 0
    costs = []
    for right, height in enumerate(heights):
        drop_old(low, left)
        if not low or height <= -low[0][0]:
            heapq.heappush(low, (-height, right))
            low_count += 1
            low_sum += height
        else:
            heapq.heappush(high, (height, right))
            high_count += 1
            high_sum += height
        if right - left + 1 > w:
            out = heights[left]
            drop_old(low, left)
            if out <= -low[0][0]:
                low_count -= 1
                low_sum -= out
            else:
                high_count -= 1
                high_sum -= out
            left += 1
        while low_count > high_count + 1:
            drop_old(low, left)
            minus_height, index = heapq.heappop(low)
            moved = -minus_height
            heapq.heappush(high, (moved, index))
            low_count -= 1
            low_sum -= moved
            high_count += 1
            high_sum += moved
        while high_count > low_count:
            drop_old(high, left)
            moved, index = heapq.heappop(high)
            heapq.heappush(low, (-moved, index))
            high_count -= 1
            high_sum -= moved
            low_count += 1
            low_sum += moved
        if right - left + 1 == w:
            drop_old(low, left)
            middle = -low[0][0]
            costs.append((middle * low_count - low_sum) + (high_sum - middle * high_count))
    return costs
