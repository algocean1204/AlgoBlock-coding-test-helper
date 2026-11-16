# 언어 함정: python.true_division
def planted(trees, holes, gap):
    count = 0
    last = -10**10  # 지금 보는 구덩이 바로 앞에 있는 나무의 위치(앞에 나무가 없으면 아주 먼 곳)
    i = 0  # trees[i]: 지금 보는 구덩이 뒤에 오는 첫 큰 나무
    for hole in holes:
        while i < len(trees) and trees[i] < hole:  # 구덩이보다 앞에 있는 큰 나무를 지나간다
            last = trees[i]
            i += 1
        next_tree = trees[i] if i < len(trees) else 10**10  # 뒤에 큰 나무가 없으면 아주 먼 곳
        # 앞 나무와도, 뒤에 오는 큰 나무와도 gap 이상 떨어져야 심는다
        if hole - last >= gap and next_tree - hole >= gap:
            count += 1
            last = hole
    return count


def solution(trees, holes, count):
    trees = sorted(trees)
    holes = sorted(holes)
    left = 1
    right = max(trees[-1], holes[-1]) - min(trees[0], holes[0])
    for i in range(len(trees) - 1):  # 큰 나무끼리의 간격은 바꿀 수 없으므로 답은 이보다 클 수 없다
        right = min(right, trees[i + 1] - trees[i])
    answer = 1
    while left <= right:
        mid = (left + right) / 2
        if planted(trees, holes, mid) >= count:  # count그루보다 많이 심을 수 있으면 몇 그루를 덜 심으면 된다
            answer = mid
            left = mid + 1
        else:
            right = mid - 1
    return answer
