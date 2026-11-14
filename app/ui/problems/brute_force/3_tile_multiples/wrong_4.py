# 틀린 까닭: 타일을 모두 쓰는 길이만 만들고 더 짧은 수를 빠뜨린다
from itertools import permutations


def solution(tiles, m):
    numbers = set()
    for order in permutations(tiles):
        if order[0] == "0":
            continue
        numbers.add(int("".join(order)))
    count = 0
    for x in numbers:
        if x % m == 0:
            count += 1
    return count
