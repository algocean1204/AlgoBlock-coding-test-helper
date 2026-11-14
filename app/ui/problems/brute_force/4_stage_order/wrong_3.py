# 틀린 까닭: 가장 많은 장르가 절반을 넘지 않으면 모든 순서가 된다고 보고 서로 다른 순서의 수(n! ÷ 같은 장르 수의 곱)를 그대로 센다
from math import factorial


def solution(genres):
    count = {}
    for genre in genres:
        count[genre] = count.get(genre, 0) + 1
    if max(count.values()) > (len(genres) + 1) // 2:
        return 0
    ways = factorial(len(genres))
    for same in count.values():
        ways //= factorial(same)
    return ways
