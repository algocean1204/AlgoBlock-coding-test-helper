// 언어 함정: javascript.fill_shared
function solution(floor) {
    const rows = floor.length, cols = floor[0].length;
    let startR = 0, startC = 0;
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            if (floor[r][c] === 'S') { startR = r; startC = c; }
        }
    }
    // distance[r][c]: 출발 칸에서 (r, c)까지의 이동 횟수. -1은 아직 가 보지 않은 칸
    const distance = new Array(rows).fill(new Array(cols).fill(-1));
    distance[startR][startC] = 0;
    // 큐는 배열과 읽는 위치(head)로 만든다. shift()는 느릴 수 있다
    const queue = [[startR, startC]];
    let head = 0;
    const moves = [[-1, 0], [1, 0], [0, -1], [0, 1]];
    while (head < queue.length) {
        const [r, c] = queue[head++];
        if (floor[r][c] === 'E') return distance[r][c];
        for (const [dr, dc] of moves) {
            const nr = r + dr, nc = c + dc;
            if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
            if (floor[nr][nc] === '#' || distance[nr][nc] !== -1) continue;
            distance[nr][nc] = distance[r][c] + 1; // 넣을 때 바로 적어야 같은 칸이 두 번 들어가지 않는다
            queue.push([nr, nc]);
        }
    }
    return -1;
}
