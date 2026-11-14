# 틀린 까닭: 만든 수를 중복 제거 없이 늘어놓는 방법마다 센다
from itertools import permutations


def solution(tiles, m):
    count = 0
    for length in range(2, len(tiles) + 1):
        for order in permutations(tiles, length):
            if order[0] == "0":
                continue
            if int("".join(order)) % m == 0:
                count += 1
    return count
