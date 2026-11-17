// 언어 함정: javascript.fill_shared
function solution(garden, commands) {
    const rows = garden.length, cols = garden[0].length;
    // 위, 오른쪽, 아래, 왼쪽: 시계 방향 순서. 오른쪽으로 돌면 +1, 왼쪽으로 돌면 -1
    const dr = [-1, 0, 1, 0];
    const dc = [0, 1, 0, -1];
    let row = 0, col = 0;
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            if (garden[r][c] === 'S') {
                row = r;
                col = c;
            }
        }
    }
    let direction = 0;
    const mowed = new Array(rows).fill(new Array(cols).fill(false));
    mowed[row][col] = true;
    let count = 1;
    for (const command of commands) {
        if (command === 'L') {
            direction = (direction + 3) % 4; // 왼쪽으로 한 번 = 오른쪽으로 세 번(음수의 나머지가 음수가 되는 것을 피한다)
        } else if (command === 'R') {
            direction = (direction + 1) % 4;
        } else {
            const nextRow = row + dr[direction], nextCol = col + dc[direction];
            if (nextRow >= 0 && nextRow < rows && nextCol >= 0 && nextCol < cols
                && garden[nextRow][nextCol] !== '#') {
                row = nextRow;
                col = nextCol;
                if (!mowed[row][col]) {
                    mowed[row][col] = true;
                    count++;
                }
            }
        }
    }
    return count;
}
