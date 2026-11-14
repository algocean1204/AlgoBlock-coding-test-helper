# 틀린 까닭: 글에 나머지 요구가 없는데 습관처럼 1,000,000,007로 나눈 나머지를 돌려준다
def solution(n):
    ways = [0] * (n + 1)
    ways[0] = 1
    for height in range(1, n + 1):
        for block in (1, 2, 3):
            if height - block >= 0:
                ways[height] = (ways[height] + ways[height - block]) % 1_000_000_007
    return ways[n]
