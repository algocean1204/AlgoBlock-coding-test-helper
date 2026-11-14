fn solution(pay: Vec<i32>) -> i32 {
    let n = pay.len();
    if n == 1 {
        return pay[0];
    }
    // 길이가 10만이라 재귀 대신 반복문으로 앞에서부터 채운다
    let mut best = vec![0i32; n]; // best[i]: 0 ~ i번째 날만 보고 골랐을 때 사례금 합의 최댓값
    best[0] = pay[0];
    best[1] = pay[0].max(pay[1]);
    for i in 2..n {
        let rest = best[i - 1]; // i번째 날은 쉰다
        let perform = best[i - 2] + pay[i]; // i번째 날 공연한다: 바로 앞날은 쉬었어야 한다
        best[i] = rest.max(perform);
    }
    best[n - 1]
}
