def solution(rows, cols, start, commands):
    # 주차장의 칸을 모두 집합에 담아 두고, 옮겨 갈 칸이 그 안에 있는지 본다
    cells = set()
    for r in range(rows):
        for c in range(cols):
            cells.add((r, c))
    here = (start[0], start[1])
    for command in commands:
        if command == 'N':
            there = (here[0] - 1, here[1])
        elif command == 'S':
            there = (here[0] + 1, here[1])
        elif command == 'W':
            there = (here[0], here[1] - 1)
        else:
            there = (here[0], here[1] + 1)
        if there in cells:
            here = there
    return [here[0], here[1]]
