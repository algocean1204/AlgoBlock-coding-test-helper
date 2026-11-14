fn solution(sticks: Vec<i32>) -> i32 {
    let mut count = 0;
    let n = sticks.len();
    for i in 0..n {
        for j in (i + 1)..n {
            for k in (j + 1)..n {
                // 세 막대 중 가장 긴 것과 나머지 둘의 합을 비교한다. 합은 i64로 계산해 넘침을 막는다
                let a = sticks[i] as i64;
                let b = sticks[j] as i64;
                let c = sticks[k] as i64;
                let longest = a.max(b).max(c);
                let sum = a + b + c - longest; // 가장 긴 것을 뺀 두 막대의 합
                if longest < sum {
                    count += 1;
                }
            }
        }
    }
    count
}
