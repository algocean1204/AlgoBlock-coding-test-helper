# 틀린 까닭: 쉴 곳이 없어 스택에 남은 등산객을 동쪽 끝 지점에서 쉰 것으로 센다(산책길을 벗어나 세지 않는다)
def solution(heights):
    n = len(heights)
    rests = [0] * n
    walking = []
    for j in range(n):
        while walking and heights[walking[-1]] >= heights[j]:
            walking.pop()
            rests[j] += 1
        walking.append(j)
    rests[n - 1] += len(walking) - 1  # 동쪽 끝 지점 자신은 빼고 남은 사람을 모두 끝에서 쉬게 한다
    return rests
