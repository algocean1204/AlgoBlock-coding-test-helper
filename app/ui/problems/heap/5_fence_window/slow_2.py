# 느린 까닭: 빠지는 판자를 힙에서 바로 찾아 지우고(remove) 다시 힙으로 만든다(heapify). 한 번에 구간 길이만큼 걸려 4만 × 3만 번이 넘는다
import heapq


def solution(heights, w):
    low = []   # 작은 쪽 절반(부호를 뒤집은 최대 힙)
    high = []  # 큰 쪽 절반(최소 힙)
    low_sum = high_sum = 0
    costs = []
    for right, height in enumerate(heights):
        if not low or height <= -low[0]:
            heapq.heappush(low, -height)
            low_sum += height
        else:
            heapq.heappush(high, height)
            high_sum += height
        if right >= w:
            out = heights[right - w]
            if out <= -low[0]:
                low.remove(-out)
                heapq.heapify(low)
                low_sum -= out
            else:
                high.remove(out)
                heapq.heapify(high)
                high_sum -= out
        while len(low) > len(high) + 1:
            moved = -heapq.heappop(low)
            low_sum -= moved
            heapq.heappush(high, moved)
            high_sum += moved
        while len(high) > len(low):
            moved = heapq.heappop(high)
            high_sum -= moved
            heapq.heappush(low, -moved)
            low_sum += moved
        if right >= w - 1:
            middle = -low[0]
            costs.append((middle * len(low) - low_sum) + (high_sum - middle * len(high)))
    return costs
