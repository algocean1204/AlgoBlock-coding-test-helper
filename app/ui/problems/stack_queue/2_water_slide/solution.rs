use std::collections::VecDeque;

fn solution(arrive: Vec<i32>, ride: i32, gap: i32, cap: i32) -> i32 {
    let mut sliding: VecDeque<i32> = VecDeque::new(); // 미끄럼틀 안에 있는 사람이 벗어나는 시각. 먼저 출발한 사람이 앞
    let mut next_person = 0; // 줄의 맨 앞 사람 번호
    let mut last_start = -1; // 바로 앞사람이 출발한 시각(아직 아무도 출발하지 않았으면 -1)
    let mut total = 0;
    let mut time = 0;
    while next_person < arrive.len() {
        while !sliding.is_empty() && sliding[0] == time { // 먼저 벗어난다
            sliding.pop_front();
        }
        let arrived = arrive[next_person] <= time;
        let room = (sliding.len() as i32) < cap;
        let gap_passed = last_start == -1 || time - last_start >= gap;
        if arrived && room && gap_passed { // 그다음 맨 앞 사람 한 명이 출발한다
            sliding.push_back(time + ride);
            total += time - arrive[next_person];
            last_start = time;
            next_person += 1;
        }
        time += 1;
    }
    total
}
