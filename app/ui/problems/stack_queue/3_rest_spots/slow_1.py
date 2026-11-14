# 느린 까닭: 등산객마다 동쪽으로 한 칸씩 다시 걸어 본다(높이가 계속 오르면 n × n / 2번 걷는다)
def solution(heights):
    n = len(heights)
    rests = [0] * n
    for i in range(n):
        for j in range(i + 1, n):
            if heights[j] <= heights[i]:
                rests[j] += 1
                break
    return rests
