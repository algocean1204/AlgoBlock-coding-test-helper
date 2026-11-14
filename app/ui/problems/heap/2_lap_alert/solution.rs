use std::collections::BinaryHeap;

fn solution(records: Vec<String>, k: i32) -> i32 {
    // BinaryHeap은 기본이 최대 힙이라 가장 느린 기록(k위)이 꼭대기에 온다. 부호를 뒤집을 필요가 없다
    let mut fastest: BinaryHeap<i32> = BinaryHeap::new(); // 지금까지 가장 빠른 기록 k개
    let mut alerts = 0;
    for record in &records {
        let mut parts = record.split(':');
        let minutes: i32 = parts.next().unwrap().parse().unwrap();
        let seconds: i32 = parts.next().unwrap().parse().unwrap();
        let time = minutes * 60 + seconds;
        if (fastest.len() as i32) < k {
            alerts += 1;
            fastest.push(time);
        } else if time < *fastest.peek().unwrap() { // 지금 k위보다 빨라야 한다. 같으면 먼저 들어온 기록이 앞선다
            alerts += 1;
            fastest.pop();
            fastest.push(time);
        }
    }
    alerts
}
