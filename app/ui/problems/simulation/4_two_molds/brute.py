def solution(dish, hours):
    # 칸을 (행, 열) → 글자 딕셔너리로 들고, 바뀐 것이 있는지는 따지지 않는다.
    # 칸마다 바뀌는 일은 많아야 두 번('.' → 'A'/'B'/'#', 'A'/'B' → '#')이고, 한 번 아무것도 바뀌지 않은 1시간 뒤로는
    # 계속 같으므로 2 × 칸 수만큼의 시간이 지나면 더는 바뀌지 않는다.
    n, m = len(dish), len(dish[0])
    state = {}
    for r, line in enumerate(dish):
        for c, ch in enumerate(line):
            state[(r, c)] = ch

    def around(grid, r, c):
        return [grid.get(p, '') for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))]

    for _ in range(min(hours, 2 * n * m + 1)):
        grown = dict(state)
        for (r, c), ch in state.items():
            if ch == '.':
                near = around(state, r, c)
                a, b = near.count('A'), near.count('B')
                if a > b:
                    grown[(r, c)] = 'A'
                elif b > a:
                    grown[(r, c)] = 'B'
                elif a == b and a >= 1:
                    grown[(r, c)] = '#'
        surrounded = dict(grown)
        for (r, c), ch in grown.items():
            other = {'A': 'B', 'B': 'A'}.get(ch)
            if other and around(grown, r, c).count(other) >= 3:
                surrounded[(r, c)] = '#'
        state = surrounded
    return [''.join(state[(r, c)] for c in range(m)) for r in range(n)]
