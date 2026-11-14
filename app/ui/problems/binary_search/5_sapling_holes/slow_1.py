# 느린 까닭: 최소 간격을 1부터 하나씩 늘려 가며 판정한다(간격 후보가 수억 개)
def planted(trees, holes, gap):
    count = 0
    last = -10**10
    i = 0
    for hole in holes:
        while i < len(trees) and trees[i] < hole:
            last = trees[i]
            i += 1
        next_tree = trees[i] if i < len(trees) else 10**10
        if hole - last >= gap and next_tree - hole >= gap:
            count += 1
            last = hole
    return count


def solution(trees, holes, count):
    trees = sorted(trees)
    holes = sorted(holes)
    limit = max(trees[-1], holes[-1]) - min(trees[0], holes[0])
    for i in range(len(trees) - 1):
        limit = min(limit, trees[i + 1] - trees[i])
    gap = 1
    while gap < limit and planted(trees, holes, gap + 1) >= count:
        gap += 1
    return gap
