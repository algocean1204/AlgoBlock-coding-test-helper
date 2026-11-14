use std::collections::VecDeque;

fn solution(n: i32, cables: Vec<Vec<i32>>, start: i32, offline: Vec<i32>) -> Vec<i32> {
    let n = n as usize;
    let mut neighbors: Vec<Vec<usize>> = vec![Vec::new(); n + 1];
    for cable in &cables {
        let (a, b) = (cable[0] as usize, cable[1] as usize);
        neighbors[a].push(b); // 케이블은 양쪽 방향이다
        neighbors[b].push(a);
    }
    let mut off = vec![false; n + 1]; // off[v]: v번 서버가 꺼져 있는가
    for &server in &offline {
        off[server as usize] = true;
    }

    // minute[v]: v번 서버가 파일을 받는 시각. -1은 아직(또는 끝내) 받지 못한 서버
    let start = start as usize;
    let mut minute = vec![-1i32; n + 1];
    minute[start] = 0;
    let mut queue = VecDeque::new();
    queue.push_back(start);
    while let Some(server) = queue.pop_front() {
        for &next in &neighbors[server] {
            if minute[next] == -1 && !off[next] {
                // 꺼진 서버는 받지도 보내지도 않는다
                minute[next] = minute[server] + 1;
                queue.push_back(next);
            }
        }
    }
    let latest = *minute.iter().max().unwrap(); // start번 서버가 0분이라 받지 못한 서버(-1)는 가장 큰 값이 되지 않는다
    let count = minute.iter().filter(|&&v| v == latest).count() as i32;
    vec![latest, count]
}
