use std::collections::VecDeque;

fn solution(floor: Vec<String>) -> i32 {
    let grid: Vec<Vec<u8>> = floor.iter().map(|line| line.bytes().collect()).collect();
    let rows = grid.len() as i32;
    let cols = grid[0].len() as i32;
    let (mut start_r, mut start_c) = (0usize, 0usize);
    for r in 0..rows as usize {
        for c in 0..cols as usize {
            if grid[r][c] == b'S' {
                start_r = r;
                start_c = c;
            }
        }
    }
    // distance[r][c]: 출발 칸에서 (r, c)까지의 이동 횟수. -1은 아직 가 보지 않은 칸
    let mut distance = vec![vec![-1; cols as usize]; rows as usize];
    distance[start_r][start_c] = 0;
    let mut queue = VecDeque::new();
    queue.push_back((start_r as i32, start_c as i32));
    while let Some((r, c)) = queue.pop_front() {
        if grid[r as usize][c as usize] == b'E' {
            return distance[r as usize][c as usize];
        }
        for (dr, dc) in [(-1, 0), (1, 0), (0, -1), (0, 1)] {
            let nr = r + dr;
            let nc = c + dc;
            if nr < 0 || nr >= rows || nc < 0 || nc >= cols {
                continue;
            }
            if grid[nr as usize][nc as usize] == b'#' || distance[nr as usize][nc as usize] != -1 {
                continue;
            }
            distance[nr as usize][nc as usize] = distance[r as usize][c as usize] + 1; // 넣을 때 바로 적어야 같은 칸이 두 번 들어가지 않는다
            queue.push_back((nr, nc));
        }
    }
    -1
}
