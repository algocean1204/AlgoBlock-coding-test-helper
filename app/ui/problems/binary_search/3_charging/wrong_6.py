# 틀린 까닭: 오른쪽 끝 n × 가장 빠른 충전기 시간을 int(32비트)끼리 곱해 넘친다(Java의 long right = fastest * n; 을 흉내 냄)
def to_int32(value):
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value >= 1 << 31 else value


def solution(n, chargers):
    left = 1
    right = to_int32(min(chargers) * n)
    while left < right:
        mid = (left + right) // 2
        done = 0
        for minute in chargers:
            done += mid // minute
        if done >= n:
            right = mid
        else:
            left = mid + 1
    return left
