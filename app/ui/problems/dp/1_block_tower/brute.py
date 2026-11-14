def solution(n):
    # 블록을 아래에서부터 하나씩 얹어 가며 탑을 모두 만들어 보고, 높이가 정확히 n인 것을 센다
    count = 0
    towers = [[]]
    while towers:
        tower = towers.pop()
        height = sum(tower)
        if height == n:
            count += 1
            continue
        for block in (1, 2, 3):
            if height + block <= n:
                towers.append(tower + [block])
    return count
