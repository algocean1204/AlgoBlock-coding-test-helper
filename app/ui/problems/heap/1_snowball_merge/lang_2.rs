// 언어 함정: rust.i32_wrap @ "힘의 합"
use std::cmp::Reverse;
use std::collections::BinaryHeap;

fn solution(snowballs: Vec<i32>) -> i64 {
    // BinaryHeap은 최대 힙이다. Reverse로 감싸면 가장 작은 것이 꼭대기에 온다
    // 합이 i32를 넘을 수 있어 i64로 담는다
    let mut heap = BinaryHeap::new();
    for &snowball in &snowballs {
        heap.push(Reverse(snowball));
    }
    let mut total: i32 = 0;
    while heap.len() > 1 {
        let Reverse(lightest) = heap.pop().unwrap();
        let Reverse(second) = heap.pop().unwrap();
        let merged = lightest + second;
        total += merged;
        heap.push(Reverse(merged));
    }
    total as i64
}
