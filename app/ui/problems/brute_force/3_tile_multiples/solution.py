from itertools import permutations


def solution(tiles, m):
    numbers = set()
    for length in range(2, len(tiles) + 1):  # 두 장 이상
        for order in permutations(tiles, length):
            if order[0] == "0":  # 맨 앞에 0 타일은 놓을 수 없다
                continue
            numbers.add(int("".join(order)))  # 같은 수는 집합이 한 번만 남긴다
    count = 0
    for x in numbers:
        if x % m == 0:
            count += 1
    return count
