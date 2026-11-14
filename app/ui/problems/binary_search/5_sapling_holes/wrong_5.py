# 틀린 까닭: 바로 앞 나무로 심은 묘목만 기억하고, 그 사이에 지나간 큰 나무를 앞 나무로 보지 않는다
def planted(trees, holes, gap):
    count = 0
    last = -10**10
    i = 0
    for hole in holes:
        while i < len(trees) and trees[i] < hole:
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
    for i in range(len(trees) - 1):
        right = min(right, trees[i + 1] - trees[i])
    answer = 1
    while left <= right:
        mid = (left + right) // 2
        if planted(trees, holes, mid) >= count:
            answer = mid
            left = mid + 1
        else:
            right = mid - 1
    return answer
