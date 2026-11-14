def solution(taste, look):
    # 정렬하지 않는다. 참가자마다 '맛도 모양도 나보다 높은 다른 참가자'가 있는지 모두 확인한다
    n = len(taste)
    count = 0
    for i in range(n):
        beaten = False
        for j in range(n):
            if taste[j] > taste[i] and look[j] > look[i]:
                beaten = True
        if not beaten:
            count += 1
    return count
