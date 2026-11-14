from itertools import combinations


def solution(trees, holes, count):
    best = 0
    for chosen in combinations(holes, count):
        points = sorted(list(trees) + list(chosen))
        gap = min(points[i + 1] - points[i] for i in range(len(points) - 1))
        best = max(best, gap)
    return best
