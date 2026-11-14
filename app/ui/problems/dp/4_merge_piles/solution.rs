fn solution(piles: Vec<i32>) -> i32 {
    let n = piles.len();
    let mut prefix = vec![0i32; n + 1]; // prefix[i]: piles[0] ~ piles[i - 1]의 합
    for i in 0..n {
        prefix[i + 1] = prefix[i] + piles[i];
    }
    let mut cost = vec![vec![0i32; n]; n]; // cost[i][j]: i ~ j번째 더미를 한 더미로 만드는 최소 시간
    for length in 2..=n { // 짧은 구간부터 채운다
        for i in 0..=(n - length) {
            let j = i + length - 1;
            let mut best = i32::MAX;
            for k in i..j { // 마지막에 [i, k] 더미와 [k + 1, j] 더미를 합친다
                best = best.min(cost[i][k] + cost[k + 1][j]);
            }
            cost[i][j] = best + prefix[j + 1] - prefix[i]; // 마지막 합치기에 드는 시간 = 구간 전체의 자루 수
        }
    }
    cost[0][n - 1]
}
