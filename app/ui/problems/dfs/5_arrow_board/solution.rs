use std::collections::HashMap;

fn solution(board: Vec<String>) -> i64 {
    let grid: Vec<Vec<u8>> = board.iter().map(|line| line.bytes().collect()).collect();
    let rows = grid.len() as i32;
    let cols = grid[0].len() as i32;
    let step = HashMap::from([(b'U', (-1, 0)), (b'D', (1, 0)), (b'L', (0, -1)), (b'R', (0, 1))]);
    const NEW: u8 = 0; // 아직 안 감
    const ON_PATH: u8 = 1; // 지금 걷는 길 위
    const DONE: u8 = 2; // 점수가 정해짐
    let mut state = vec![vec![NEW; cols as usize]; rows as usize];
    let mut order = vec![vec![0usize; cols as usize]; rows as usize]; // 지금 길에서 몇 번째로 밟은 칸인가
    let mut score = vec![vec![0i64; cols as usize]; rows as usize];
    for start_r in 0..rows {
        for start_c in 0..cols {
            if state[start_r as usize][start_c as usize] == DONE {
                continue;
            }
            // 1. 밖으로 나가거나, 점수가 정해진 칸에 닿거나, 지금 길 위의 칸에 다시 닿을 때까지 걸으며 길을 적는다
            let mut path: Vec<(usize, usize)> = Vec::new();
            let (mut r, mut c) = (start_r, start_c);
            let mut next_score: i64;
            loop {
                state[r as usize][c as usize] = ON_PATH;
                order[r as usize][c as usize] = path.len();
                path.push((r as usize, c as usize));
                let (dr, dc) = step[&grid[r as usize][c as usize]];
                r += dr;
                c += dc;
                if r < 0 || r >= rows || c < 0 || c >= cols {
                    next_score = 0; // 밖이다: 더 밟을 칸이 없다
                    break;
                }
                let (ur, uc) = (r as usize, c as usize);
                if state[ur][uc] == DONE {
                    next_score = score[ur][uc]; // 답을 아는 칸: 더 걷지 않고 이어 쓴다
                    break;
                }
                if state[ur][uc] == ON_PATH {
                    // 고리: 다시 닿은 칸부터 지금 칸까지. 고리 위의 칸은 어디서 출발하든 고리를 한 바퀴 돈다
                    let first = order[ur][uc];
                    let length = (path.len() - first) as i64;
                    for &(loop_r, loop_c) in &path[first..] {
                        score[loop_r][loop_c] = length;
                        state[loop_r][loop_c] = DONE;
                    }
                    path.truncate(first); // 남은 것은 고리로 들어가기 전의 칸들
                    next_score = length;
                    break;
                }
            }
            // 2. 걸어온 길을 거꾸로 돌아오며 '다음 칸의 점수 + 1'을 적는다
            for &(back_r, back_c) in path.iter().rev() {
                next_score += 1;
                score[back_r][back_c] = next_score;
                state[back_r][back_c] = DONE;
            }
        }
    }
    score.iter().map(|row| row.iter().sum::<i64>()).sum() // 합은 최대 약 6백억이라 i64
}
