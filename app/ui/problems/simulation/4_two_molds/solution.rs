fn solution(dish: Vec<String>, hours: i32) -> Vec<String> {
    let (n, m) = (dish.len() as i32, dish[0].len() as i32);
    let mut board: Vec<Vec<u8>> = dish.iter().map(|line| line.bytes().collect()).collect();

    // grid에서 (r, c)와 맞닿은 칸 가운데 mold인 칸의 수
    let count = |grid: &Vec<Vec<u8>>, r: usize, c: usize, mold: u8| -> i32 {
        let mut total = 0;
        for (dr, dc) in [(-1, 0), (1, 0), (0, -1), (0, 1)] {
            let nr = r as i32 + dr;
            let nc = c as i32 + dc;
            if nr >= 0 && nr < n && nc >= 0 && nc < m && grid[nr as usize][nc as usize] == mold {
                total += 1;
            }
        }
        total
    };

    for _ in 0..hours {
        // 1단계(번식): 1시간이 시작될 때의 board를 보고, 결과는 grown에 적는다
        let mut grown = board.clone();
        for r in 0..n as usize {
            for c in 0..m as usize {
                if board[r][c] != b'.' {
                    continue;
                }
                let a = count(&board, r, c, b'A');
                let b = count(&board, r, c, b'B');
                if a > b {
                    grown[r][c] = b'A';
                } else if b > a {
                    grown[r][c] = b'B';
                } else if a > 0 {
                    grown[r][c] = b'#';
                }
            }
        }
        // 2단계(포위): 1단계가 끝난 grown을 보고, 결과는 result에 적는다
        let mut result = grown.clone();
        for r in 0..n as usize {
            for c in 0..m as usize {
                if grown[r][c] == b'A' && count(&grown, r, c, b'B') >= 3 {
                    result[r][c] = b'#';
                } else if grown[r][c] == b'B' && count(&grown, r, c, b'A') >= 3 {
                    result[r][c] = b'#';
                }
            }
        }
        if result == board {
            break; // 1시간 동안 아무것도 바뀌지 않았으면 그 뒤로도 계속 같다
        }
        board = result;
    }
    board.iter().map(|row| String::from_utf8(row.clone()).unwrap()).collect()
}
