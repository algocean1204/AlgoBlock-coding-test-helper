fn solution(rows: i32, cols: i32, works: Vec<Vec<i32>>) -> i32 {
    // 인덱스로 쓰려고 usize로 바꾼다
    let rows = rows as usize;
    let cols = cols as usize;
    // 끝 다음 칸(r2 + 1행, c2 + 1열)에도 표시해야 하므로 한 행, 한 열씩 크게 만든다
    let mut diff: Vec<Vec<i32>> = vec![vec![0; cols + 1]; rows + 1];
    for work in &works {
        let (r1, c1) = (work[0] as usize, work[1] as usize);
        let (r2, c2) = (work[2] as usize, work[3] as usize);
        let amount = work[4];
        diff[r1][c1] += amount;
        diff[r1][c2 + 1] -= amount;
        diff[r2 + 1][c1] -= amount;
        diff[r2 + 1][c2 + 1] += amount;
    }
    // 가로로 누적: 같은 행 안에서 왼쪽 표시를 오른쪽으로 펼친다
    for r in 0..=rows {
        for c in 1..=cols {
            diff[r][c] += diff[r][c - 1];
        }
    }
    // 세로로 누적: 같은 열 안에서 위쪽 표시를 아래로 펼친다
    for r in 1..=rows {
        for c in 0..=cols {
            diff[r][c] += diff[r - 1][c];
        }
    }
    let mut count = 0;
    for r in 0..rows {
        for c in 0..cols {
            if diff[r][c] == 0 {
                count += 1;
            }
        }
    }
    count
}
