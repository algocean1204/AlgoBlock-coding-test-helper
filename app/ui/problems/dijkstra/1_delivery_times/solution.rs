use std::cmp::Reverse;
use std::collections::BinaryHeap;

fn solution(n: i32, roads: Vec<Vec<i32>>) -> Vec<i32> {
    let n = n as usize;
    let mut graph: Vec<Vec<(usize, i32)>> = vec![vec![]; n + 1];
    for road in &roads {
        let (a, b, time) = (road[0] as usize, road[1] as usize, road[2]);
        graph[a].push((b, time));
        graph[b].push((a, time));
    }

    let inf = i32::MAX;  // 최대 시간은 약 6억이라 i32로 충분하다
    let mut dist = vec![inf; n + 1];
    dist[1] = 0;
    // Rust의 BinaryHeap은 최대 힙이라 Reverse로 감싸 작은 시간부터 꺼낸다
    let mut heap = BinaryHeap::new();
    heap.push(Reverse((0, 1usize)));
    while let Some(Reverse((d, now))) = heap.pop() {
        if d > dist[now] {
            continue;  // 이미 더 짧은 시간으로 확정된 마을
        }
        for &(nxt, time) in &graph[now] {
            if d + time < dist[nxt] {
                dist[nxt] = d + time;
                heap.push(Reverse((dist[nxt], nxt)));
            }
        }
    }
    dist[1..].to_vec()
}
