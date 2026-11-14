# 틀린 까닭: 출발 지점이 아니라 바로 앞 지점보다 낮거나 같은 곳(처음 만나는 내리막)에서 쉰다
def solution(heights):
    n = len(heights)
    rests = [0] * n
    for i in range(n):
        for j in range(i + 1, n):
            if heights[j] <= heights[j - 1]:
                rests[j] += 1
                break
    return rests
