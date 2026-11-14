# 느린 까닭: 구간의 (최댓값, 최솟값)을 메모하지 않고 재귀로 매번 다시 구한다(수가 n개면 호출이 약 3^n번)
def solution(values, signs):
    def best(i, j):
        if i == j:
            return values[i], values[i]
        high, low = float('-inf'), float('inf')
        for k in range(i, j):
            left_high, left_low = best(i, k)
            right_high, right_low = best(k + 1, j)
            if signs[k] == '+':
                high = max(high, left_high + right_high)
                low = min(low, left_low + right_low)
            elif signs[k] == '-':
                high = max(high, left_high - right_low)
                low = min(low, left_low - right_high)
            else:
                high = max(high, max(left_high, right_high))
                low = min(low, max(left_low, right_low))
        return high, low

    return list(best(0, len(values) - 1))
