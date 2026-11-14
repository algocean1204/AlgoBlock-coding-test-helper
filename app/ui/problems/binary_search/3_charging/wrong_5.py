# 틀린 까닭: 판정 중 충전한 대수의 합을 int(32비트)로 쌓아 20억을 넘으면 넘친다(Java의 int done; done += mid / c; 를 흉내 냄)
def to_int32(value):
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value >= 1 << 31 else value


def solution(n, chargers):
    left = 1
    right = min(chargers) * n
    while left < right:
        mid = (left + right) // 2
        done = 0
        for minute in chargers:
            done = to_int32(done + mid // minute)
        if done >= n:
            right = mid
        else:
            left = mid + 1
    return left
