fn solution(board: Vec<Vec<i32>>, k: i32) -> Vec<Vec<i32>> {
    let n = board.len();
    let m = board[0].len();
    let mut result = board.clone();
    for ring in 0..n.min(m) / 2 {
        let (top, bottom, left, right) = (ring, n - 1 - ring, ring, m - 1 - ring);
        // 고리의 칸을 왼쪽 위 모서리부터 시계 방향 순서로 늘어놓는다
        let mut cells: Vec<(usize, usize)> = Vec::new();
        for c in left..=right {
            cells.push((top, c));
        }
        for r in top + 1..=bottom {
            cells.push((r, right));
        }
        for c in (left..right).rev() {
            cells.push((bottom, c));
        }
        for r in (top + 1..bottom).rev() {
            cells.push((r, left));
        }
        let length = cells.len();
        let mut shift = k as usize % length; // 칸 수만큼 돌면 제자리로 돌아온다
        if ring % 2 == 1 {
            shift = (length - shift) % length; // 반시계 방향으로 shift칸 = 시계 방향으로 length - shift칸(usize라 음수를 피해야 한다)
        }
        // 시계 방향으로 shift칸 돌면 i번째 칸의 보석은 i + shift번째 칸으로 간다
        for i in 0..length {
            let (r, c) = cells[(i + shift) % length];
            result[r][c] = board[cells[i].0][cells[i].1];
        }
    }
    result
}
