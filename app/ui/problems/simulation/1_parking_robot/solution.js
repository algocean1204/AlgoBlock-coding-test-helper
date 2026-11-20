function solution(rows, cols, start, commands) {
    const move = { N: [-1, 0], S: [1, 0], W: [0, -1], E: [0, 1] };
    let row = start[0], col = start[1];
    for (const command of commands) {
        const [dr, dc] = move[command];
        const nextRow = row + dr, nextCol = col + dc;
        if (nextRow >= 0 && nextRow < rows && nextCol >= 0 && nextCol < cols) {
            row = nextRow;
            col = nextCol;
        }
    }
    return [row, col];
}
