def solution(floor):
    # 물 칸마다 번호표를 붙이고, 맞닿은 칸끼리 더 작은 번호표로 맞추기를 바뀌는 것이 없을 때까지 되풀이한다.
    # 끝나면 같은 웅덩이의 칸은 모두 같은 번호표를 갖는다. 서로 다른 번호표의 수가 웅덩이 수다.
    rows, cols = len(floor), len(floor[0])
    label = {}
    for r in range(rows):
        for c in range(cols):
            if floor[r][c] == '#':
                label[(r, c)] = r * cols + c
    changed = True
    while changed:
        changed = False
        for (r, c) in label:
            for other in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if other in label and label[other] < label[(r, c)]:
                    label[(r, c)] = label[other]
                    changed = True
    return len(set(label.values()))
