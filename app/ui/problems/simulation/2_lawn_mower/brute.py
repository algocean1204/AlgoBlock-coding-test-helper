def solution(garden, commands):
    # 방향을 글자로 들고, 돌 때마다 표에서 다음 방향을 찾는다. 지나간 칸은 좌표 집합에 모은다
    turn_left = {'up': 'left', 'left': 'down', 'down': 'right', 'right': 'up'}
    turn_right = {'up': 'right', 'right': 'down', 'down': 'left', 'left': 'up'}
    step = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}
    grass = set()
    for r, line in enumerate(garden):
        for c, ch in enumerate(line):
            if ch != '#':
                grass.add((r, c))
            if ch == 'S':
                here = (r, c)
    facing = 'up'
    visited = {here}
    for command in commands:
        if command == 'L':
            facing = turn_left[facing]
        elif command == 'R':
            facing = turn_right[facing]
        else:
            there = (here[0] + step[facing][0], here[1] + step[facing][1])
            if there in grass:
                here = there
                visited.add(here)
    return len(visited)
