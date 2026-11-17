// 언어 함정: javascript.fill_shared
function solution(rows, cols, works) {
    // 끝 다음 칸(r2 + 1행, c2 + 1열)에도 표시해야 하므로 한 행, 한 열씩 크게 만든다
    const diff = new Array(rows + 1).fill(new Array(cols + 1).fill(0));
    for (const [r1, c1, r2, c2, amount] of works) {
        diff[r1][c1] += amount;
        diff[r1][c2 + 1] -= amount;
        diff[r2 + 1][c1] -= amount;
        diff[r2 + 1][c2 + 1] += amount;
    }
    // 가로로 누적: 같은 행 안에서 왼쪽 표시를 오른쪽으로 펼친다
    for (let r = 0; r <= rows; r++) {
        for (let c = 1; c <= cols; c++) {
            diff[r][c] += diff[r][c - 1];
        }
    }
    // 세로로 누적: 같은 열 안에서 위쪽 표시를 아래로 펼친다
    for (let r = 1; r <= rows; r++) {
        for (let c = 0; c <= cols; c++) {
            diff[r][c] += diff[r - 1][c];
        }
    }
    let count = 0;
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            if (diff[r][c] === 0) {
                count++;
            }
        }
    }
    return count;
}
