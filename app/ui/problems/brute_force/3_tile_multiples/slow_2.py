# 느린 까닭: 만든 수를 리스트에 모으며 이미 있는지 in으로 확인한다(수가 10만 개 가까이 쌓이면 확인 한 번에 리스트 전체를 훑는다)
from itertools import permutations


def solution(tiles, m):
    numbers = []
    for length in range(2, len(tiles) + 1):
        for order in permutations(tiles, length):
            if order[0] == "0":
                continue
            x = int("".join(order))
            if x not in numbers:
                numbers.append(x)
    count = 0
    for x in numbers:
        if x % m == 0:
            count += 1
    return count
