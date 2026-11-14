fn solution(n: i32) -> i64 {
    // 탑의 수는 i32 범위를 넘으므로 i64로 담는다
    let n = n as usize;
    let mut ways = vec![0i64; n + 1]; // ways[h]: 높이가 정확히 h인 탑의 수
    ways[0] = 1; // 아무것도 쌓지 않은 높이 0의 탑 하나
    for height in 1..=n {
        for block in 1..=3 { // 맨 위에 놓은 블록의 높이
            if height >= block {
                ways[height] += ways[height - block];
            }
        }
    }
    ways[n]
}
