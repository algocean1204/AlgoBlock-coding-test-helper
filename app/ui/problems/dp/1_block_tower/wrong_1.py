# 틀린 까닭: 높이 1, 2 블록만 생각해 바로 아래 두 높이의 답만 더한다(높이 3 블록을 빠뜨린다)
def solution(n):
    ways = [0] * (n + 1)
    ways[0] = 1
    for height in range(1, n + 1):
        ways[height] = ways[height - 1]
        if height >= 2:
            ways[height] += ways[height - 2]
    return ways[n]
