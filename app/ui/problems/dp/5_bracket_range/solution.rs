fn solution(values: Vec<i32>, signs: String) -> Vec<i32> {
    let n = values.len();
    let signs = signs.as_bytes();
    let mut big = vec![vec![0i32; n]; n]; // big[i][j]: values[i] ~ values[j]를 괄호로 묶어 만들 수 있는 가장 큰 값
    let mut small = vec![vec![0i32; n]; n]; // small[i][j]: 같은 구간의 가장 작은 값
    for i in 0..n {
        big[i][i] = values[i];
        small[i][i] = values[i];
    }
    for length in 2..=n { // 짧은 구간부터 채운다
        for i in 0..=(n - length) {
            let j = i + length - 1;
            let mut best = i32::MIN;
            let mut worst = i32::MAX;
            for k in i..j { // signs[k]를 맨 마지막에 계산한다: [i, k]와 [k + 1, j]로 나뉜다
                let (high, low);
                if signs[k] == b'+' {
                    high = big[i][k] + big[k + 1][j];
                    low = small[i][k] + small[k + 1][j];
                } else if signs[k] == b'-' {
                    high = big[i][k] - small[k + 1][j]; // 빼는 쪽은 가장 작을 때 결과가 가장 크다
                    low = small[i][k] - big[k + 1][j];
                } else { // '^': 두 값 가운데 큰 값
                    high = big[i][k].max(big[k + 1][j]);
                    low = small[i][k].max(small[k + 1][j]); // 큰 값을 작게 하려면 양쪽을 모두 작게 한다
                }
                best = best.max(high);
                worst = worst.min(low);
            }
            big[i][j] = best;
            small[i][j] = worst;
        }
    }
    vec![big[0][n - 1], small[0][n - 1]]
}
