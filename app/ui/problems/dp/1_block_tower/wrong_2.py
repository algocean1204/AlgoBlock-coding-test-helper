# 틀린 까닭: 블록 종류를 바깥 반복으로 돌려, 순서만 다른 탑(1+2와 2+1)을 한 가지로 센다
def solution(n):
    ways = [0] * (n + 1)
    ways[0] = 1
    for block in (1, 2, 3):
        for height in range(block, n + 1):
            ways[height] += ways[height - block]
    return ways[n]
