# 틀린 까닭: 팔 수 있는 기한을 빼먹고 남은 빵을 언제까지나 판다
def solution(baked, want, fresh):
    stock = 0
    sold = 0
    for day in range(len(baked)):
        stock += baked[day]
        take = min(stock, want[day])
        stock -= take
        sold += take
    return sold
