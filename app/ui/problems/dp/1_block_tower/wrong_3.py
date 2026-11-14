# 틀린 까닭: 시작값을 손으로 적으며 높이 3을 3가지로 적는다(높이 3 블록 하나만 쓴 탑을 빠뜨린다)
def solution(n):
    ways = [0] * (n + 4)
    ways[1], ways[2], ways[3] = 1, 2, 3
    for height in range(4, n + 1):
        ways[height] = ways[height - 1] + ways[height - 2] + ways[height - 3]
    return ways[n]
