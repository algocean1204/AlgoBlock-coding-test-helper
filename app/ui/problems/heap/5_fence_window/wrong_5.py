# 틀린 까닭: 왼쪽 판자를 빼기 전에 개수를 맞추고, 뺀 뒤에는 다시 맞추지 않는다(두 힙의 개수가 어긋난 채 가운데를 읽는다)
import heapq


def drop_old(heap, left):
    # 규칙 하나: 꼭대기를 보거나 꺼내기 전에는 언제나 이것을 부른다.
    # 꼭대기에 창 밖으로 나간 판자(번호 < left)가 있으면 버린다. 힙 안쪽에 있는 것은 꼭대기에 올라올 때 버린다
    while heap and heap[0][1] < left:
        heapq.heappop(heap)


def solution(heights, w):
    # low: 작은 쪽 절반. 파이썬 힙은 가장 작은 것이 꼭대기라, 높이에 -를 붙인 (-높이, 번호)로 넣어 가장 높은 판자가 꼭대기에 오게 한다
    # high: 큰 쪽 절반. (높이, 번호) 그대로 넣어 가장 낮은 판자가 꼭대기에 온다
    low = []
    high = []
    in_low = [False] * len(heights)  # 판자마다 지금 low에 들어 있는지
    low_count = high_count = 0       # 창 안에 남은 판자 수. 지울 표시만 한 판자가 힙에 남아 있어 len()과 다르다
    low_sum = high_sum = 0
    left = 0                         # 창의 맨 왼쪽 번호. 이보다 작은 번호는 창 밖이다
    costs = []
    for right, height in enumerate(heights):
        # 1. 새 판자를 넣는다(4단계와 같다)
        drop_old(low, left)
        if not low or height <= -low[0][0]:
            heapq.heappush(low, (-height, right))
            in_low[right] = True
            low_count += 1
            low_sum += height
        else:
            heapq.heappush(high, (height, right))
            high_count += 1
            high_sum += height
        # 3. 개수 맞추기: low_count가 high_count와 같거나 하나 더 많게. 옮기기 전에 꼭대기의 나간 판자를 버린다
        while low_count > high_count + 1:
            drop_old(low, left)
            minus_height, index = heapq.heappop(low)
            moved = -minus_height  # low에는 -높이로 들어 있으므로 원래 높이로 되돌린다
            heapq.heappush(high, (moved, index))
            in_low[index] = False
            low_count -= 1
            low_sum -= moved
            high_count += 1
            high_sum += moved
        while high_count > low_count:
            drop_old(high, left)
            moved, index = heapq.heappop(high)
            heapq.heappush(low, (-moved, index))
            in_low[index] = True
            high_count -= 1
            high_sum -= moved
            low_count += 1
            low_sum += moved
        # 2. 창이 w개를 넘으면 맨 왼쪽 판자를 뺀다. 힙에서 바로 지우지 않고 개수와 합에서만 뺀다
        if right - left + 1 > w:
            if in_low[left]:
                low_count -= 1
                low_sum -= heights[left]
            else:
                high_count -= 1
                high_sum -= heights[left]
            left += 1
        # 4. 창이 w개로 찼으면 가운데 높이(low의 꼭대기)로 맞추는 비용을 잰다
        if right - left + 1 == w:
            drop_old(low, left)
            middle = -low[0][0]
            costs.append((middle * low_count - low_sum) + (high_sum - middle * high_count))
    return costs
