use std::cmp::Reverse;
use std::collections::{BinaryHeap, HashMap};

fn solution(routes: Vec<String>, start: String, goal: String) -> i32 {
    // 선착장 이름마다 0부터 번호를 매기고, 번호로 인접 목록을 만든다
    let mut id: HashMap<String, usize> = HashMap::new();
    let mut graph: Vec<Vec<(usize, i32)>> = Vec::new();
    for route in &routes {
        let part: Vec<&str> = route.split(' ').collect();
        let mut ids = [0usize; 2];
        for i in 0..2 {
            if !id.contains_key(part[i]) {
                id.insert(part[i].to_string(), id.len());
                graph.push(Vec::new());
            }
            ids[i] = id[part[i]];
        }
        let minutes: i32 = part[2].parse().unwrap();
        graph[ids[0]].push((ids[1], minutes));
    }

    let source = id[&start];
    let target = id[&goal];
    let mut dist = vec![i32::MAX; id.len()];  // 최대 시간은 6천만 정도라 i32로 충분하다
    dist[source] = 0;
    // Rust의 BinaryHeap은 최대 힙이라 Reverse로 감싸 작은 시간부터 꺼낸다
    let mut heap = BinaryHeap::new();
    heap.push(Reverse((0, source)));
    while let Some(Reverse((d, now))) = heap.pop() {
        if d > dist[now] {
            continue;  // 이미 더 빠른 시간으로 확정된 선착장
        }
        if now == target {
            return d;  // 도착점은 큐에서 꺼낼 때 확정된다
        }
        for &(nxt, minutes) in &graph[now] {
            if d + minutes < dist[nxt] {
                dist[nxt] = d + minutes;
                heap.push(Reverse((dist[nxt], nxt)));
            }
        }
    }
    -1
}
