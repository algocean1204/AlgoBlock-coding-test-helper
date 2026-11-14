# 틀린 까닭: trees와 holes를 정렬하지 않고 주어진 순서대로 훑어, 이웃하지 않은 나무끼리 간격을 잰다
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
    left = 1
    right = max(max(trees), max(holes)) - min(min(trees), min(holes))
    for i in range(len(trees) - 1):
        right = min(right, abs(trees[i + 1] - trees[i]))
    answer = 1
    while left <= right:
        mid = (left + right) // 2
        if planted(trees, holes, mid) >= count:
            answer = mid
            left = mid + 1
        else:
            right = mid - 1
    return answer
