# 언어 함정: python.negative_index
def solution(n):
    ways = [0] * (n + 1)  # ways[h]: 높이가 정확히 h인 탑의 수
    ways[0] = 1  # 아무것도 쌓지 않은 높이 0의 탑 하나
    for height in range(1, n + 1):
        for block in (1, 2, 3):  # 맨 위에 놓은 블록의 높이
            ways[height] += ways[height - block]
    return ways[n]
