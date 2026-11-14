# 틀린 까닭: d일에 구운 빵을 d + fresh일까지 팔 수 있다고 본다(d + fresh - 1일까지다)
def solution(baked, want, fresh):
    n = len(baked)
    left = list(baked)
    oldest = 0
    sold = 0
    for day in range(n):
        oldest = max(oldest, day - fresh)
        need = want[day]
        while need > 0 and oldest <= day:
            take = min(need, left[oldest])
            left[oldest] -= take
            need -= take
            sold += take
            if left[oldest] == 0:
                oldest += 1
    return sold
