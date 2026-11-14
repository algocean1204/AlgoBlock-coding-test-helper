# 틀린 까닭: 스택 맨 위를 한 번만 보고 꺼낸다(조건이 맞는 동안 연달아 꺼내야 한다)
def solution(heights):
    n = len(heights)
    rests = [0] * n
    walking = []
    for j in range(n):
        if walking and heights[walking[-1]] >= heights[j]:
            walking.pop()
            rests[j] += 1
        walking.append(j)
    return rests
