# 느린 까닭: 매번 남은 놀이기구 전체를 훑어 다음에 고칠 것을 찾는다(n × n)
def solution(fix, line, walk):
    left = list(range(len(fix)))
    now = 0
    total = 0
    first = True
    while left:
        best = 0
        for k in range(1, len(left)):
            a, b = left[k], left[best]
            if (fix[a] + walk) * line[b] < (fix[b] + walk) * line[a]:
                best = k
        ride = left.pop(best)
        if not first:
            now += walk
        first = False
        now += fix[ride]
        total += now * line[ride]
    return total
