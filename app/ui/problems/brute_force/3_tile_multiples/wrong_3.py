# 틀린 까닭: 맨 앞에 0 타일을 놓은 배치를 정수로 바꿔 0이 떨어진 수로 센다
from itertools import permutations


def solution(tiles, m):
    numbers = set()
    for length in range(2, len(tiles) + 1):
        for order in permutations(tiles, length):
            numbers.add(int("".join(order)))
    count = 0
    for x in numbers:
        if x % m == 0:
            count += 1
    return count
