// 언어 함정: javascript.fill_shared
function solution(building) {
    const rows = building.length, cols = building[0].length;
    const moves = [[-1, 0], [1, 0], [0, -1], [0, 1]];

    // 1. 불: 불이 난 칸을 모두 처음부터 큐에 넣고 한 번에 퍼뜨린다(여러 출발점 BFS)
    // fire[r][c]: 불이 (r, c)에 닿는 시각. -1은 불이 끝내 닿지 않는 칸
    // 큐는 배열과 읽는 위치(head)로 만든다. shift()는 느릴 수 있다
    const fire = new Array(rows).fill(new Array(cols).fill(-1));
    let queue = [];
    let startR = 0, startC = 0;
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            if (building[r][c] === 'F') {
                fire[r][c] = 0;
                queue.push([r, c]);
            } else if (building[r][c] === 'S') {
                startR = r;
                startC = c;
            }
        }
    }
    let head = 0;
    while (head < queue.length) {
        const [r, c] = queue[head++];
        for (const [dr, dc] of moves) {
            const nr = r + dr, nc = c + dc;
            if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && building[nr][nc] !== '#' && fire[nr][nc] === -1) {
                fire[nr][nc] = fire[r][c] + 1;
                queue.push([nr, nc]);
            }
        }
    }

    // 2. 사람: 불보다 먼저 닿는 칸으로만 움직이는 BFS
    const person = Array.from({ length: rows }, () => new Array(cols).fill(-1));
    person[startR][startC] = 0;
    queue = [[startR, startC]];
    head = 0;
    while (head < queue.length) {
        const [r, c] = queue[head++];
        for (const [dr, dc] of moves) {
            const nr = r + dr, nc = c + dc;
            if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
            if (building[nr][nc] === '#' || person[nr][nc] !== -1) continue;
            const arrive = person[r][c] + 1;
            if (fire[nr][nc] !== -1 && fire[nr][nc] <= arrive) continue; // 불이 같은 분이나 더 일찍 닿는 칸은 못 들어간다
            if (building[nr][nc] === 'E') return arrive;
            person[nr][nc] = arrive;
            queue.push([nr, nc]);
        }
    }
    return -1;
}
