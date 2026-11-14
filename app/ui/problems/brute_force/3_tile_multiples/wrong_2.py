# 틀린 까닭: 타일 한 장만 쓴 수도 센다
from itertools import permutations


def solution(tiles, m):
    numbers = set()
    for length in range(1, len(tiles) + 1):
        for order in permutations(tiles, length):
            if order[0] == "0":
                continue
            numbers.add(int("".join(order)))
    count = 0
    for x in numbers:
        if x % m == 0:
            count += 1
    return count
