# 느린 까닭: 10부터 만들 수 있는 가장 큰 수까지 모든 수를 하나씩 보며 타일로 만들 수 있는지 확인한다(타일 8장이면 1억 개 가까운 수를 본다)
from collections import Counter


def solution(tiles, m):
    have = Counter(tiles)
    count = 0
    for x in range(10, 10 ** len(tiles)):
        if x % m != 0:
            continue
        need = Counter(str(x))
        if all(need[digit] <= have[digit] for digit in need):
            count += 1
    return count
