use std::cmp::Reverse;
use std::collections::BinaryHeap;

fn solution(n: i32, rules: Vec<Vec<i32>>) -> Vec<i32> {
    let n = n as usize;
    let mut after: Vec<Vec<usize>> = vec![Vec::new(); n + 1]; // after[a]: a를 설치해야 설치할 수 있는 패키지들
    let mut waiting = vec![0; n + 1]; // waiting[b]: b보다 먼저 설치해야 하는데 아직 설치하지 않은 패키지 수(진입 차수)
    for r in &rules {
        after[r[0] as usize].push(r[1] as usize);
        waiting[r[1] as usize] += 1;
    }

    // Rust의 BinaryHeap은 큰 것이 먼저 나오므로 Reverse로 감싸 작은 것이 먼저 나오게 한다
    let mut ready = BinaryHeap::new();
    for p in 1..=n {
        if waiting[p] == 0 {
            ready.push(Reverse(p));
        }
    }
    let mut order: Vec<i32> = Vec::new();
    while let Some(Reverse(pkg)) = ready.pop() {
        order.push(pkg as i32);
        for &nxt in &after[pkg] {
            waiting[nxt] -= 1;
            if waiting[nxt] == 0 {
                ready.push(Reverse(nxt));
            }
        }
    }

    if order.len() < n {
        return Vec::new(); // 끝내 설치할 수 없는 패키지가 남았다: 규칙에 사이클이 있다
    }
    order
}
