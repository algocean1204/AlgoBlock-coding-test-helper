fn solution(sticks: Vec<i32>) -> i32 {
    let mut count = 0;
    let n = sticks.len();
    for i in 0..n {
        for j in (i + 1)..n {
            for k in (j + 1)..n {
                let mut three = [sticks[i], sticks[j], sticks[k]];
                three.sort(); // 작은 것부터 늘어놓으면 마지막이 가장 긴 막대다
                let (shortest, middle, longest) = (three[0], three[1], three[2]);
                if longest < shortest + middle {
                    count += 1;
                }
            }
        }
    }
    count
}
