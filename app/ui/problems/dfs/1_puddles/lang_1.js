// 언어 함정: javascript.fill_shared
function solution(floor) {
    const rows = floor.length, cols = floor[0].length;
    const visited = new Array(rows).fill(new Array(cols).fill(false));
    const moves = [[-1, 0], [1, 0], [0, -1], [0, 1]];
    let count = 0;
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            if (floor[r][c] !== '#' || visited[r][c]) continue;
            // 아직 어느 웅덩이에도 들지 않은 물 칸: 새 웅덩이를 하나 세고, 이어진 칸을 모두 방문 표시한다
            count++;
            visited[r][c] = true;
            const stack = [[r, c]];
            while (stack.length > 0) {
                const [nowR, nowC] = stack.pop();
                for (const [dr, dc] of moves) {
                    const nextR = nowR + dr, nextC = nowC + dc;
                    if (nextR < 0 || nextR >= rows || nextC < 0 || nextC >= cols) continue; // 바닥 밖
                    if (floor[nextR][nextC] === '#' && !visited[nextR][nextC]) {
                        visited[nextR][nextC] = true;
                        stack.push([nextR, nextC]);
                    }
                }
            }
        }
    }
    return count;
}
