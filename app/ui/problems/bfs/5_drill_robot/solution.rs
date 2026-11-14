use std::collections::VecDeque;

fn solution(mine: Vec<Vec<i32>>, drill: i32) -> i32 {
    let rows = mine.len() as i32;
    let cols = mine[0].len() as i32;
    let moves = [(-1, 0), (1, 0), (0, -1), (0, 1)];

    // 상태 = (행, 열, 지금까지 쓴 드릴 수). 같은 칸이라도 쓴 드릴 수가 다르면 다른 상태다
    // distance[r][c][used]: 그 상태까지의 최소 이동 횟수. -1은 아직 가 보지 않은 상태
    let mut distance = vec![vec![vec![-1i32; drill as usize + 1]; cols as usize]; rows as usize];
    distance[0][0][0] = 0;
    let mut queue: VecDeque<(i32, i32, i32)> = VecDeque::new();
    queue.push_back((0, 0, 0));
    while let Some((r, c, used)) = queue.pop_front() {
        let here = distance[r as usize][c as usize][used as usize];
        if r == rows - 1 && c == cols - 1 {
            return here;
        }
        for (dr, dc) in moves {
            let nr = r + dr;
            let nc = c + dc;
            if nr < 0 || nr >= rows || nc < 0 || nc >= cols {
                continue;
            }
            let next_used = used + mine[nr as usize][nc as usize]; // 바위 칸이면 드릴을 한 번 더 쓴다
            if next_used > drill {
                continue;
            }
            if distance[nr as usize][nc as usize][next_used as usize] != -1 {
                continue;
            }
            distance[nr as usize][nc as usize][next_used as usize] = here + 1;
            queue.push_back((nr, nc, next_used));
        }
    }
    -1
}
