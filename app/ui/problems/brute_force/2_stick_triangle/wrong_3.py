# 틀린 까닭: 길이가 같은 세 막대 묶음을 한 번만 센다(번호가 다른 막대를 같은 막대로 본다)
def solution(sticks):
    seen = set()
    n = len(sticks)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                three = sorted([sticks[i], sticks[j], sticks[k]])
                if three[2] < three[0] + three[1]:
                    seen.add(tuple(three))
    return len(seen)
