# 틀린 까닭: 표를 n+1칸으로 만들고 높이 1, 2, 3의 시작값부터 적어서 n이 1, 2일 때 칸이 모자라 오류가 난다
def solution(n):
    ways = [0] * (n + 1)
    ways[1] = 1
    ways[2] = 2
    ways[3] = 4
    for height in range(4, n + 1):
        ways[height] = ways[height - 1] + ways[height - 2] + ways[height - 3]
    return ways[n]
