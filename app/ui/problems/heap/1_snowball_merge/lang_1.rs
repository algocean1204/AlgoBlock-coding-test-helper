// 언어 함정: rust.max_heap @ "가장 가벼운 것과 두 번째로 가벼운 것"
use std::collections::BinaryHeap;

fn solution(snowballs: Vec<i32>) -> i64 {
    // BinaryHeap은 최대 힙이다. Reverse로 감싸면 가장 작은 것이 꼭대기에 온다
    // 합이 i32를 넘을 수 있어 i64로 담는다
    let mut heap: BinaryHeap<i64> = BinaryHeap::new();
    for &snowball in &snowballs {
        heap.push(snowball as i64);
    }
    let mut total: i64 = 0;
    while heap.len() > 1 {
        let lightest = heap.pop().unwrap();
        let second = heap.pop().unwrap();
        let merged = lightest + second;
        total += merged;
        heap.push(merged);
    }
    total
}
