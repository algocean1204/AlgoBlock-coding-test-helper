function solution(mine, drill) {
    const rows = mine.length, cols = mine[0].length;
    const moves = [[-1, 0], [1, 0], [0, -1], [0, 1]];

    // 상태 = (행, 열, 지금까지 쓴 드릴 수). 같은 칸이라도 쓴 드릴 수가 다르면 다른 상태다
    // distance[r][c][used]: 그 상태까지의 최소 이동 횟수. -1은 아직 가 보지 않은 상태
    const distance = Array.from({ length: rows }, () =>
        Array.from({ length: cols }, () => new Array(drill + 1).fill(-1)));
    distance[0][0][0] = 0;
    // 큐는 배열과 읽는 위치(head)로 만든다. shift()는 느릴 수 있다
    const queue = [[0, 0, 0]];
    let head = 0;
    while (head < queue.length) {
        const [r, c, used] = queue[head++];
        if (r === rows - 1 && c === cols - 1) return distance[r][c][used];
        for (const [dr, dc] of moves) {
            const nr = r + dr, nc = c + dc;
            if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
            const nextUsed = used + mine[nr][nc]; // 바위 칸이면 드릴을 한 번 더 쓴다
            if (nextUsed > drill) continue;
            if (distance[nr][nc][nextUsed] !== -1) continue;
            distance[nr][nc][nextUsed] = distance[r][c][used] + 1;
            queue.push([nr, nc, nextUsed]);
        }
    }
    return -1;
}
