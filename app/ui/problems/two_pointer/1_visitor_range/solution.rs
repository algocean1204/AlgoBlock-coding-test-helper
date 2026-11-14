fn solution(visitors: Vec<i32>, queries: Vec<Vec<i32>>) -> Vec<i32> {
    // prefix[i]: 1일부터 i일까지 방문자 수의 합. prefix[0]은 아무 날도 더하지 않은 0
    // 합은 최대 10만 × 1만 = 10억이라 i32에 들어간다
    let mut prefix: Vec<i32> = vec![0; visitors.len() + 1];
    for i in 0..visitors.len() {
        prefix[i + 1] = prefix[i] + visitors[i];
    }
    let mut answer: Vec<i32> = Vec::new();
    for query in &queries {
        let start = query[0] as usize; // 인덱스로 쓰려고 usize로 바꾼다
        let end = query[1] as usize;
        answer.push(prefix[end] - prefix[start - 1]);
    }
    answer
}
