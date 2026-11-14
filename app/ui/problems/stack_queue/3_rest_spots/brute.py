def solution(heights):
    n = len(heights)
    rests = [0] * n
    for j in range(n):
        # j번에서 쉬는 등산객: j보다 서쪽에서 출발해, 출발 지점과 j 사이에 쉴 곳이 없고, j가 쉴 곳인 사람
        for i in range(j):
            between = [k for k in range(i + 1, j) if heights[k] <= heights[i]]
            if not between and heights[j] <= heights[i]:
                rests[j] += 1
    return rests
