def solution(building):
    # 큐를 쓰지 않는다: 1분마다 불이 붙은 칸 전체와 사람이 있을 수 있는 칸 전체를 글 그대로 한꺼번에 옮긴다
    rows, cols = len(building), len(building[0])
    open_cells = {(r, c) for r in range(rows) for c in range(cols) if building[r][c] != "#"}

    def around(cell):
        r, c = cell
        return [x for x in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)) if x in open_cells]

    burning = {cell for cell in open_cells if building[cell[0]][cell[1]] == "F"}
    here = {cell for cell in open_cells if building[cell[0]][cell[1]] == "S"}
    for minute in range(1, rows * cols + 2):  # 가장 짧은 대피 길은 같은 칸을 두 번 지나지 않는다
        burning = burning | {nxt for cell in burning for nxt in around(cell)}
        here = {nxt for cell in here for nxt in around(cell) if nxt not in burning}
        if any(building[r][c] == "E" for r, c in here):
            return minute
        if not here:
            return -1
    return -1
