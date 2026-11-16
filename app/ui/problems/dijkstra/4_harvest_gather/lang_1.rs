// 언어 함정: rust.max_heap @ "가장 이른 시각"
use std::collections::BinaryHeap;

const INF: i64 = 1 << 60; // 시간 합이 i32를 넘으므로 i64, 더해도 넘치지 않게 넉넉히

fn dijkstra(graph: &Vec<Vec<(usize, i64)>>, n: usize, start: usize) -> Vec<i64> {
    let mut dist = vec![INF; n + 1];
    dist[start] = 0;
    let mut heap = BinaryHeap::new();
    heap.push((0i64, start));
    while let Some((d, now)) = heap.pop() {
        if d > dist[now] {
            continue;
        }
        for &(nxt, time) in &graph[now] {
            if d + time < dist[nxt] {
                dist[nxt] = d + time;
                heap.push((dist[nxt], nxt));
            }
        }
    }
    dist
}

fn solution(n: i32, roads: Vec<Vec<i32>>, farms: Vec<i32>, market: i32) -> i64 {
    let n = n as usize;
    let mut small = vec![Vec::new(); n + 1]; // 작은 트럭: u → v, slow분
    let mut big_back = vec![Vec::new(); n + 1]; // 큰 트럭의 도로를 거꾸로 뒤집은 것: v → u, fast분
    for r in &roads {
        let (u, v) = (r[0] as usize, r[1] as usize);
        small[u].push((v, r[2] as i64));
        big_back[v].push((u, r[3] as i64));
    }

    // 뒤집은 그래프에서 시장으로부터의 거리 = 각 마을에서 시장까지 큰 트럭이 걸리는 시간
    let to_market = dijkstra(&big_back, n, market as usize);

    let mut gather = vec![0i64; n + 1]; // gather[m]: 작은 트럭이 모두 m번 마을에 모이는 시각(가장 늦게 도착한 트럭)
    for &farm in &farms {
        let arrive = dijkstra(&small, n, farm as usize);
        for m in 1..=n {
            gather[m] = gather[m].max(arrive[m]);
        }
    }

    let mut answer = INF;
    for m in 1..=n {
        // 모이는 마을을 모두 해 본다. 닿지 못하는 곳은 무한대라 뽑히지 않는다
        if gather[m] < INF && to_market[m] < INF {
            answer = answer.min(gather[m] + to_market[m]);
        }
    }
    if answer < INF {
        answer
    } else {
        -1
    }
}
