use std::collections::BinaryHeap;

fn solution(pickup: Vec<i32>, minutes: Vec<i32>, booked: Vec<i32>) -> Vec<i32> {
    let n = pickup.len();
    let mut must = vec![false; n]; // 꼭 받아야 하는 주문인가
    for &b in &booked {
        must[b as usize] = true;
    }
    let mut order: Vec<usize> = (0..n).collect();
    order.sort_by_key(|&i| pickup[i]); // 찾으러 오는 시각이 이른 주문부터
    let mut can_drop = BinaryHeap::new(); // Rust의 BinaryHeap은 기본이 최대 힙이라 가장 긴 것이 먼저 나온다
    let mut count = 0; // 받은 주문 수
    let mut total: i64 = 0; // 받은 주문을 쉬지 않고 모두 만들면 끝나는 시각 (넘치지 않게 i64)
    for &i in &order {
        count += 1;
        total += minutes[i] as i64;
        if !must[i] {
            can_drop.push(minutes[i]);
        }
        while total > pickup[i] as i64 && !can_drop.is_empty() {
            // 늦는다: 가장 오래 걸리는 것부터 되무른다
            total -= can_drop.pop().unwrap() as i64;
            count -= 1;
        }
        if total > pickup[i] as i64 {
            return vec![-1, -1]; // 꼭 받아야 하는 주문끼리도 지킬 수 없다
        }
    }
    vec![count, total as i32]
}
