use std::cmp::Reverse;
use std::collections::BinaryHeap;

fn solution(patients: Vec<Vec<i32>>) -> i64 {
    let n = patients.len();
    // (도착 시각, 진료 시간, 위급도, 번호). 튜플은 앞에서부터 차례로 비교하며 정렬된다
    let mut arrivals: Vec<(i32, i32, i32, usize)> = Vec::new();
    for (i, p) in patients.iter().enumerate() {
        arrivals.push((p[0], p[1], p[2], i));
    }
    arrivals.sort();
    // 도착한 동물: (-위급도, 진료 시간, 번호, 도착 시각). 부호를 뒤집어 위급도가 큰 것이 먼저 나오게 하고,
    // BinaryHeap은 최대 힙이라 Reverse로 감싸 가장 작은 튜플이 꼭대기에 오게 한다
    let mut waiting: BinaryHeap<Reverse<(i32, i32, usize, i32)>> = BinaryHeap::new();
    let mut time = 0;
    let mut next_arrival = 0; // arrivals에서 아직 힙에 넣지 않은 첫 자리
    let mut total: i64 = 0; // 기다린 시간의 합은 i32를 넘을 수 있다
    for _ in 0..n {
        if waiting.is_empty() && arrivals[next_arrival].0 > time {
            time = arrivals[next_arrival].0; // 도착한 동물이 없으면 다음 동물이 올 때까지 건너뛴다
        }
        while next_arrival < n && arrivals[next_arrival].0 <= time {
            let (arrive, duration, grade, i) = arrivals[next_arrival];
            waiting.push(Reverse((-grade, duration, i, arrive)));
            next_arrival += 1;
        }
        let Reverse((_grade, duration, _i, arrive)) = waiting.pop().unwrap();
        total += (time - arrive) as i64;
        time += duration;
    }
    total
}
