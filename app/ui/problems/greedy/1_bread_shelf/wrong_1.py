# 틀린 까닭: 그날 구운 빵부터 판다(오래된 빵이 먼저 버려지므로 오래된 빵부터 팔아야 한다)
def solution(baked, want, fresh):
    n = len(baked)
    left = list(baked)
    sold = 0
    for day in range(n):
        need = want[day]
        for d in range(day, max(0, day - fresh + 1) - 1, -1):
            take = min(need, left[d])
            left[d] -= take
            need -= take
            sold += take
    return sold
