// 언어 함정: javascript.float_division
function solution(board) {
    const rows = board.length, cols = board[0].length;
    const NEW = 0, ON_PATH = 1, DONE = 2; // 아직 안 감 / 지금 걷는 길 위 / 점수가 정해짐
    const state = Array.from({ length: rows }, () => new Array(cols).fill(NEW));
    const order = Array.from({ length: rows }, () => new Array(cols).fill(0)); // 지금 길에서 몇 번째로 밟은 칸인가
    const score = Array.from({ length: rows }, () => new Array(cols).fill(0));
    for (let startR = 0; startR < rows; startR++) {
        for (let startC = 0; startC < cols; startC++) {
            if (state[startR][startC] === DONE) continue;
            // 1. 밖으로 나가거나, 점수가 정해진 칸에 닿거나, 지금 길 위의 칸에 다시 닿을 때까지 걸으며 길을 적는다
            let path = []; // 칸 번호 = 행 * cols + 열
            let r = startR, c = startC;
            let nextScore;
            while (true) {
                state[r][c] = ON_PATH;
                order[r][c] = path.length;
                path.push(r * cols + c);
                const arrow = board[r][c];
                if (arrow === 'U') r--;
                else if (arrow === 'D') r++;
                else if (arrow === 'L') c--;
                else c++;
                if (r < 0 || r >= rows || c < 0 || c >= cols) {
                    nextScore = 0; // 밖이다: 더 밟을 칸이 없다
                    break;
                }
                if (state[r][c] === DONE) {
                    nextScore = score[r][c]; // 답을 아는 칸: 더 걷지 않고 이어 쓴다
                    break;
                }
                if (state[r][c] === ON_PATH) {
                    // 고리: 다시 닿은 칸부터 지금 칸까지. 고리 위의 칸은 어디서 출발하든 고리를 한 바퀴 돈다
                    const first = order[r][c];
                    const length = path.length - first;
                    for (let i = first; i < path.length; i++) {
                        const loopR = Math.floor(path[i] / cols), loopC = path[i] % cols;
                        score[loopR][loopC] = length;
                        state[loopR][loopC] = DONE;
                    }
                    path = path.slice(0, first); // 남은 것은 고리로 들어가기 전의 칸들
                    nextScore = length;
                    break;
                }
            }
            // 2. 걸어온 길을 거꾸로 돌아오며 '다음 칸의 점수 + 1'을 적는다
            for (let i = path.length - 1; i >= 0; i--) {
                nextScore++;
                const backR = path[i] / cols, backC = path[i] % cols;
                score[backR][backC] = nextScore;
                state[backR][backC] = DONE;
            }
        }
    }
    let total = 0; // 합은 최대 약 6백억이라 2^53보다 훨씬 작아 Number로 충분하다
    for (const row of score) for (const s of row) total += s;
    return total;
}
