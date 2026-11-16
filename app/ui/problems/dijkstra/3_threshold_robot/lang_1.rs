// 언어 함정: rust.max_heap @ "가장 높은 턱의 높이가 가장 낮은 길"
use std::collections::BinaryHeap;

fn solution(ground: Vec<Vec<i32>>) -> i32 {
    let rows = ground.len();
    let cols = ground[0].len();
    // 그 칸까지 가는 길에서 넘는 가장 높은 턱의 최솟값
    let mut highest = vec![vec![i32::MAX; cols]; rows];
    highest[0][0] = 0;
    // Rust의 BinaryHeap은 최대 힙이라 Reverse로 감싸 낮은 턱부터 꺼낸다
    let mut heap = BinaryHeap::new();
    heap.push((0, 0usize, 0usize));
    while let Some((h, r, c)) = heap.pop() {
        if h > highest[r][c] {
            continue;
        }
        if r == rows - 1 && c == cols - 1 {
            return h;
        }
        // usize는 음수가 안 돼서, 행·열을 i32로 바꿔 이웃을 구한다
        for (dr, dc) in [(-1i32, 0i32), (1, 0), (0, -1), (0, 1)] {
            let nr = r as i32 + dr;
            let nc = c as i32 + dc;
            if nr >= 0 && nr < rows as i32 && nc >= 0 && nc < cols as i32 {
                let (nr, nc) = (nr as usize, nc as usize);
                let ledge = (ground[nr][nc] - ground[r][c]).abs();
                let cur = h.max(ledge); // 합이 아니라 가장 높은 턱
                if cur < highest[nr][nc] {
                    highest[nr][nc] = cur;
                    heap.push((cur, nr, nc));
                }
            }
        }
    }
    highest[rows - 1][cols - 1]
}
