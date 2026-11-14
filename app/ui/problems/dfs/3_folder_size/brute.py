def solution(parent, files, limit):
    # 정의 그대로: i번 폴더의 전체 용량은, parent를 따라 바깥으로 나가다 i번을 만나는 폴더 j(i 자신 포함)의 files[j]를 모두 더한 값이다
    n = len(parent)
    count = 0
    for i in range(n):
        total = 0
        for j in range(n):
            k = j
            while k != -1:
                if k == i:
                    total += files[j]
                    break
                k = parent[k]
        if total >= limit:
            count += 1
    return count
