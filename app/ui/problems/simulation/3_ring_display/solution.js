function solution(board, k) {
    const n = board.length, m = board[0].length;
    const result = board.map(row => row.slice());
    for (let ring = 0; ring < Math.floor(Math.min(n, m) / 2); ring++) {
        const top = ring, bottom = n - 1 - ring, left = ring, right = m - 1 - ring;
        // 고리의 칸을 왼쪽 위 모서리부터 시계 방향 순서로 늘어놓는다
        const cells = [];
        for (let c = left; c <= right; c++) cells.push([top, c]);
        for (let r = top + 1; r <= bottom; r++) cells.push([r, right]);
        for (let c = right - 1; c >= left; c--) cells.push([bottom, c]);
        for (let r = bottom - 1; r > top; r--) cells.push([r, left]);
        const values = cells.map(([r, c]) => board[r][c]);
        const length = cells.length;
        let shift = k % length; // 칸 수만큼 돌면 제자리로 돌아온다
        if (ring % 2 === 1) {
            shift = (length - shift) % length; // 반시계 방향으로 shift칸 = 시계 방향으로 length - shift칸(음수의 나머지를 피한다)
        }
        // 시계 방향으로 shift칸 돌면 i번째 칸의 보석은 i + shift번째 칸으로 간다
        for (let i = 0; i < length; i++) {
            const [r, c] = cells[(i + shift) % length];
            result[r][c] = values[i];
        }
    }
    return result;
}
