function solution(rows, cols, start, commands) {
    let row = start[0], col = start[1];
    for (const command of commands) {
        let dr = 0, dc = 0;
        if (command === 'N') dr = -1;
        else if (command === 'S') dr = 1;
        else if (command === 'W') dc = -1;
        else dc = 1;
        const nextRow = row + dr, nextCol = col + dc;
        if (nextRow >= 0 && nextRow < rows && nextCol >= 0 && nextCol < cols) {
            row = nextRow;
            col = nextCol;
        }
    }
    return [row, col];
}
