# 틀린 까닭: 빵을 사지 못한 손님이 다음 날 다시 온다고 본다(돌아간 손님은 다시 오지 않는다)
def solution(baked, want, fresh):
    n = len(baked)
    left = list(baked)
    oldest = 0
    sold = 0
    need = 0
    for day in range(n):
        oldest = max(oldest, day - fresh + 1)
        need += want[day]
        while need > 0 and oldest <= day:
            take = min(need, left[oldest])
            left[oldest] -= take
            need -= take
            sold += take
            if left[oldest] == 0:
                oldest += 1
    return sold
