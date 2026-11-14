# 틀린 까닭: 높이가 같은 지점에서는 쉬지 않는다고 본다(낮거나 같은 지점에서 쉰다)
def solution(heights):
    n = len(heights)
    rests = [0] * n
    walking = []
    for j in range(n):
        while walking and heights[walking[-1]] > heights[j]:
            walking.pop()
            rests[j] += 1
        walking.append(j)
    return rests
