# 틀린 까닭: 묘목을 심을 자리만 따지고 큰 나무끼리의 간격을 보지 않아, 답이 가장 가까운 두 큰 나무의 간격보다 커진다
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
    left = 1
    right = max(trees[-1], holes[-1]) - min(trees[0], holes[0])
    answer = 1
    while left <= right:
        mid = (left + right) // 2
        if planted(trees, holes, mid) >= count:
            answer = mid
            left = mid + 1
        else:
            right = mid - 1
    return answer
