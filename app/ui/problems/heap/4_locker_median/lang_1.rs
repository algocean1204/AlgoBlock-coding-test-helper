// 언어 함정: rust.max_heap @ "거리를 더한 값이 가장 작아지는 곳"
use std::collections::BinaryHeap;

fn solution(houses: Vec<i32>) -> i64 {
    // BinaryHeap은 기본이 최대 힙이라 low는 그대로 쓰면 가장 큰 값이 꼭대기에 온다. 부호를 뒤집을 필요가 없다
    let mut low: BinaryHeap<i64> = BinaryHeap::new(); // 작은 쪽 절반
    let mut high: BinaryHeap<i64> = BinaryHeap::new(); // 큰 쪽 절반
    // 거리 합은 i32를 넘을 수 있어 모두 i64로 둔다
    let mut low_sum: i64 = 0;
    let mut high_sum: i64 = 0;
    let mut total: i64 = 0;
    for &h in &houses {
        let house = h as i64;
        if low.is_empty() || house <= *low.peek().unwrap() {
            low.push(house);
            low_sum += house;
        } else {
            high.push(house);
            high_sum += house;
        }
        // 개수 맞추기: low가 high와 같거나 하나 더 많게 둔다. 그러면 low의 꼭대기가 가운데 값이다
        if low.len() > high.len() + 1 {
            let moved = low.pop().unwrap();
            low_sum -= moved;
            high.push(moved);
            high_sum += moved;
        } else if high.len() > low.len() {
            let moved = high.pop().unwrap();
            high_sum -= moved;
            low.push(moved);
            low_sum += moved;
        }
        let middle = *low.peek().unwrap();
        // (작은 쪽 집들에서 가운데까지의 거리 합) + (큰 쪽 집들에서 가운데까지의 거리 합)
        total += (middle * low.len() as i64 - low_sum) + (high_sum - middle * high.len() as i64);
    }
    total
}
