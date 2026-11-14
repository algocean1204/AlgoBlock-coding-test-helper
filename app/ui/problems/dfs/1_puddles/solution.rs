fn solution(floor: Vec<String>) -> i32 {
    let grid: Vec<Vec<u8>> = floor.iter().map(|line| line.bytes().collect()).collect();
    let rows = grid.len() as i32;
    let cols = grid[0].len() as i32;
    let mut visited = vec![vec![false; cols as usize]; rows as usize];
    let mut count = 0;
    for r in 0..rows {
        for c in 0..cols {
            if grid[r as usize][c as usize] != b'#' || visited[r as usize][c as usize] {
                continue;
            }
            // 아직 어느 웅덩이에도 들지 않은 물 칸: 새 웅덩이를 하나 세고, 이어진 칸을 모두 방문 표시한다
            count += 1;
            visited[r as usize][c as usize] = true;
            let mut stack = vec![(r, c)];
            while let Some((now_r, now_c)) = stack.pop() {
                for (dr, dc) in [(-1, 0), (1, 0), (0, -1), (0, 1)] {
                    let next_r = now_r + dr;
                    let next_c = now_c + dc;
                    if next_r < 0 || next_r >= rows || next_c < 0 || next_c >= cols {
                        continue; // 바닥 밖
                    }
                    let (ur, uc) = (next_r as usize, next_c as usize);
                    if grid[ur][uc] == b'#' && !visited[ur][uc] {
                        visited[ur][uc] = true;
                        stack.push((next_r, next_c));
                    }
                }
            }
        }
    }
    count
}
