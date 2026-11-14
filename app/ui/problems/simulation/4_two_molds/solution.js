function solution(dish, hours) {
    const n = dish.length, m = dish[0].length;
    let board = dish.map(line => line.split(''));

    // grid에서 (r, c)와 맞닿은 칸 가운데 mold인 칸의 수
    function count(grid, r, c, mold) {
        let total = 0;
        for (const [nr, nc] of [[r - 1, c], [r + 1, c], [r, c - 1], [r, c + 1]]) {
            if (nr >= 0 && nr < n && nc >= 0 && nc < m && grid[nr][nc] === mold) total++;
        }
        return total;
    }

    for (let hour = 0; hour < hours; hour++) {
        // 1단계(번식): 1시간이 시작될 때의 board를 보고, 결과는 grown에 적는다
        const grown = board.map(row => row.slice());
        for (let r = 0; r < n; r++) {
            for (let c = 0; c < m; c++) {
                if (board[r][c] !== '.') continue;
                const a = count(board, r, c, 'A'), b = count(board, r, c, 'B');
                if (a > b) grown[r][c] = 'A';
                else if (b > a) grown[r][c] = 'B';
                else if (a > 0) grown[r][c] = '#';
            }
        }
        // 2단계(포위): 1단계가 끝난 grown을 보고, 결과는 result에 적는다
        const result = grown.map(row => row.slice());
        for (let r = 0; r < n; r++) {
            for (let c = 0; c < m; c++) {
                if (grown[r][c] === 'A' && count(grown, r, c, 'B') >= 3) result[r][c] = '#';
                else if (grown[r][c] === 'B' && count(grown, r, c, 'A') >= 3) result[r][c] = '#';
            }
        }
        // 1시간 동안 아무것도 바뀌지 않았으면 그 뒤로도 계속 같다(배열끼리는 ===로 비교할 수 없어 글자로 합쳐 비교한다)
        if (result.map(row => row.join('')).join('\n') === board.map(row => row.join('')).join('\n')) break;
        board = result;
    }
    return board.map(row => row.join(''));
}
