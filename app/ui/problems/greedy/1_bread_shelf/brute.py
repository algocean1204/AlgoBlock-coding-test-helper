def solution(baked, want, fresh):
    # 빵 한 개, 손님 한 명을 하나씩 늘어놓고, 손님마다 살 수 있는 빵을 이어 주는 최대 짝짓기(증가 경로)를 구한다
    loaves = [d for d in range(len(baked)) for _ in range(baked[d])]  # 빵마다 구운 날
    guests = [d for d in range(len(want)) for _ in range(want[d])]    # 손님마다 온 날
    owner = [-1] * len(loaves)  # owner[b]: b번 빵을 산 손님

    def can(g, b):
        return loaves[b] <= guests[g] <= loaves[b] + fresh - 1

    def assign(g, seen):
        for b in range(len(loaves)):
            if can(g, b) and not seen[b]:
                seen[b] = True
                if owner[b] == -1 or assign(owner[b], seen):
                    owner[b] = g
                    return True
        return False

    return sum(1 for g in range(len(guests)) if assign(g, [False] * len(loaves)))
