from itertools import combinations


def solution(sticks):
    count = 0
    for a, b, c in combinations(sticks, 3):
        if a + b > c and a + c > b and b + c > a:
            count += 1
    return count
