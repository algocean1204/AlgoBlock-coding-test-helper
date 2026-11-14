fn solution(garden: Vec<String>, commands: String) -> i32 {
    let grid: Vec<Vec<u8>> = garden.iter().map(|line| line.bytes().collect()).collect();
    let rows = grid.len() as i32;
    let cols = grid[0].len() as i32;
    // 위, 오른쪽, 아래, 왼쪽: 시계 방향 순서. 오른쪽으로 돌면 +1, 왼쪽으로 돌면 -1
    let dr = [-1, 0, 1, 0];
    let dc = [0, 1, 0, -1];
    let mut row = 0i32;
    let mut col = 0i32;
    for r in 0..rows {
        for c in 0..cols {
            if grid[r as usize][c as usize] == b'S' {
                row = r;
                col = c;
            }
        }
    }
    let mut direction = 0usize;
    let mut mowed = vec![vec![false; cols as usize]; rows as usize];
    mowed[row as usize][col as usize] = true;
    let mut count = 1;
    for command in commands.chars() {
        if command == 'L' {
            direction = (direction + 3) % 4; // 왼쪽으로 한 번 = 오른쪽으로 세 번(usize라 음수를 피해야 한다)
        } else if command == 'R' {
            direction = (direction + 1) % 4;
        } else {
            let next_row = row + dr[direction];
            let next_col = col + dc[direction];
            if next_row >= 0 && next_row < rows && next_col >= 0 && next_col < cols
                && grid[next_row as usize][next_col as usize] != b'#'
            {
                row = next_row;
                col = next_col;
                if !mowed[row as usize][col as usize] {
                    mowed[row as usize][col as usize] = true;
                    count += 1;
                }
            }
        }
    }
    count
}
