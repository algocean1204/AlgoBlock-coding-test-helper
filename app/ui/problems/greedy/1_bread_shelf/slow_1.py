# 느린 까닭: 날마다 팔 수 있는 날들을 가장 오래된 날부터 다시 훑는다(다 팔린 날도 매번 다시 지나 n × fresh번에 가깝다)
def solution(baked, want, fresh):
    n = len(baked)
    left = list(baked)
    sold = 0
    for day in range(n):
        need = want[day]
        for d in range(max(0, day - fresh + 1), day + 1):
            if need == 0:
                break
            take = min(need, left[d])
            left[d] -= take
            need -= take
            sold += take
    return sold
