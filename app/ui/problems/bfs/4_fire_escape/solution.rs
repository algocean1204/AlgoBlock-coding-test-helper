use std::collections::VecDeque;

fn solution(building: Vec<String>) -> i32 {
    let grid: Vec<Vec<u8>> = building.iter().map(|line| line.bytes().collect()).collect();
    let rows = grid.len() as i32;
    let cols = grid[0].len() as i32;
    let moves = [(-1, 0), (1, 0), (0, -1), (0, 1)];

    // 1. 불: 불이 난 칸을 모두 처음부터 큐에 넣고 한 번에 퍼뜨린다(여러 출발점 BFS)
    // fire[r][c]: 불이 (r, c)에 닿는 시각. -1은 불이 끝내 닿지 않는 칸
    let mut fire = vec![vec![-1i32; cols as usize]; rows as usize];
    let mut queue: VecDeque<(i32, i32)> = VecDeque::new();
    let (mut start_r, mut start_c) = (0i32, 0i32);
    for r in 0..rows {
        for c in 0..cols {
            let ch = grid[r as usize][c as usize];
            if ch == b'F' {
                fire[r as usize][c as usize] = 0;
                queue.push_back((r, c));
            } else if ch == b'S' {
                start_r = r;
                start_c = c;
            }
        }
    }
    while let Some((r, c)) = queue.pop_front() {
        for (dr, dc) in moves {
            let nr = r + dr;
            let nc = c + dc;
            if nr >= 0 && nr < rows && nc >= 0 && nc < cols
                && grid[nr as usize][nc as usize] != b'#'
                && fire[nr as usize][nc as usize] == -1
            {
                fire[nr as usize][nc as usize] = fire[r as usize][c as usize] + 1;
                queue.push_back((nr, nc));
            }
        }
    }

    // 2. 사람: 불보다 먼저 닿는 칸으로만 움직이는 BFS
    let mut person = vec![vec![-1i32; cols as usize]; rows as usize];
    person[start_r as usize][start_c as usize] = 0;
    queue.push_back((start_r, start_c));
    while let Some((r, c)) = queue.pop_front() {
        for (dr, dc) in moves {
            let nr = r + dr;
            let nc = c + dc;
            if nr < 0 || nr >= rows || nc < 0 || nc >= cols {
                continue;
            }
            let (ur, uc) = (nr as usize, nc as usize);
            if grid[ur][uc] == b'#' || person[ur][uc] != -1 {
                continue;
            }
            let arrive = person[r as usize][c as usize] + 1;
            if fire[ur][uc] != -1 && fire[ur][uc] <= arrive {
                continue; // 불이 같은 분이나 더 일찍 닿는 칸은 못 들어간다
            }
            if grid[ur][uc] == b'E' {
                return arrive;
            }
            person[ur][uc] = arrive;
            queue.push_back((nr, nc));
        }
    }
    -1
}
