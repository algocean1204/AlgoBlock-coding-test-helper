fn solution(n: i32, tracks: Vec<Vec<i32>>, queries: Vec<Vec<i32>>) -> Vec<i32> {
    let n = n as usize;
    const INF: i64 = 1_000_000_000; // 가장 긴 최단 시간(299,000)보다 크고, 두 번 더해도 넘치지 않게 i64로 둔다
    let mut dist = vec![vec![INF; n + 1]; n + 1];
    for s in 1..=n {
        dist[s][s] = 0;
    }
    for t in &tracks {
        let (a, b, minutes) = (t[0] as usize, t[1] as usize, t[2] as i64);
        if minutes < dist[a][b] { // 같은 두 역 사이 선로가 여럿이면 짧은 것만 남긴다
            dist[a][b] = minutes;
            dist[b][a] = minutes;
        }
    }

    let mut asked: Vec<Vec<usize>> = vec![Vec::new(); n + 1]; // asked[k]: k번 역까지 열렸을 때를 묻는 질문의 번호들
    for (index, q) in queries.iter().enumerate() {
        asked[q[0] as usize].push(index);
    }

    let mut answer = vec![0; queries.len()];
    for k in 1..=n {
        // 플로이드: k번 역을 거쳐 가는 길로 모든 두 역 사이 거리를 고친다(아직 닫힌 역까지의 거리도 고쳐 둔다)
        for i in 1..=n {
            for j in 1..=n {
                if dist[i][k] + dist[k][j] < dist[i][j] {
                    dist[i][j] = dist[i][k] + dist[k][j];
                }
            }
        }
        // 이제 dist[a][b]는 1~k번 역만 거쳐 가는 가장 짧은 시간이다
        for &index in &asked[k] {
            let d = dist[queries[index][1] as usize][queries[index][2] as usize];
            answer[index] = if d >= INF { -1 } else { d as i32 };
        }
    }
    answer
}
