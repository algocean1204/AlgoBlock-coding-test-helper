// 언어 함정: rust.max_heap @ "통행료 합의 최솟값"
use std::collections::BinaryHeap;

fn solution(n: i32, roads: Vec<Vec<i32>>, k: i32) -> i32 {
    let n = n as usize;
    let k = k as usize;
    let mut graph: Vec<Vec<(usize, i32)>> = vec![vec![]; n + 1];
    for road in &roads {
        let (u, v, toll) = (road[0] as usize, road[1] as usize, road[2]);
        graph[u].push((v, toll));
        graph[v].push((u, toll));
    }

    // dist[city][used][just]: 통행권을 used장 쓰고 city에 왔을 때 낸 통행료 합의 최솟값(최대 약 1억6천만이라 i32로 충분)
    // just는 바로 앞 도로에 통행권을 썼으면 1, 통행료를 냈으면(또는 아직 출발 전이면) 0
    let mut dist = vec![vec![[i32::MAX; 2]; k + 1]; n + 1];
    dist[1][0][0] = 0;
    // Rust의 BinaryHeap은 최대 힙이라 Reverse로 감싸 작은 통행료부터 꺼낸다
    let mut heap = BinaryHeap::new();
    heap.push((0, 1usize, 0usize, 0usize));
    while let Some((cost, city, used, just)) = heap.pop() {
        if cost > dist[city][used][just] {
            continue;
        }
        if city == n {
            return cost; // 몇 장을 썼든 n번 도시를 처음 꺼낸 값이 가장 싸다(통행권은 남겨도 된다)
        }
        for &(nxt, toll) in &graph[city] {
            if cost + toll < dist[nxt][used][0] {
                // 통행료를 낸다
                dist[nxt][used][0] = cost + toll;
                heap.push((cost + toll, nxt, used, 0));
            }
            if used < k && just == 0 && cost < dist[nxt][used + 1][1] {
                // 통행권을 쓴다(바로 앞 도로에 쓰지 않았을 때만)
                dist[nxt][used + 1][1] = cost;
                heap.push((cost, nxt, used + 1, 1));
            }
        }
    }
    -1
}
