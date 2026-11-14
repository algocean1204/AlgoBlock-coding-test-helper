# 느린 까닭: 참가자마다 다른 참가자를 모두 확인한다(아무도 떨어지지 않으면 10만 × 10만 번)
def solution(taste, look):
    n = len(taste)
    count = 0
    for i in range(n):
        beaten = False
        for j in range(n):
            if taste[j] > taste[i] and look[j] > look[i]:
                beaten = True
                break
        if not beaten:
            count += 1
    return count
