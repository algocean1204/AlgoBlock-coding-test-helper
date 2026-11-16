// 언어 함정: rust.unwrap_none
use std::collections::HashMap;

// 재귀로 쓰면 쉼터가 5만 개 한 줄일 때 스택이 넘칠 수 있다. 그래서 재귀 대신,
// '들어갈 때'와 '돌아올 때'를 스택에 따로 넣어 같은 순서를 만든다(돌아올 때는 -번호-1로 구분한다).
fn solution(trails: Vec<Vec<i32>>, energy: Vec<i32>, target: i32) -> i32 {
    let n = energy.len();
    let mut neighbors: Vec<Vec<usize>> = vec![Vec::new(); n];
    for trail in &trails {
        let (a, b) = (trail[0] as usize, trail[1] as usize);
        neighbors[a].push(b); // 어느 쪽이 위쪽인지 모르므로 양쪽에 넣는다
        neighbors[b].push(a);
    }
    let mut prefix = vec![0i32; n]; // prefix[v]: 0번부터 v번까지 길 위 energy의 합(최대 5천만이라 i32로 충분하다)
    prefix[0] = energy[0];
    // 지금 경로 위의 누적 합이 몇 번씩 있는가. 0번 위(아무 쉼터도 지나지 않은 곳)의 누적 합 0을 넣어 둔다
    let mut on_path: HashMap<i32, i32> = HashMap::new();
    on_path.insert(0, 1);
    let mut visited = vec![false; n];
    visited[0] = true;
    let mut count = 0i32; // 코스 수는 최대 n(n+1)/2 = 약 12.5억이라 i32에 들어간다
    let mut stack: Vec<i64> = vec![0];
    while let Some(top) = stack.pop() {
        if top < 0 {
            let hut = (-top - 1) as usize;
            *on_path.get_mut(&prefix[hut]).unwrap() -= 1; // 이 쉼터 아래를 다 보았다: 경로에서 뺀다
            continue;
        }
        let hut = top as usize;
        // u부터 hut까지의 합 = prefix[hut] - (u 바로 위까지의 누적 합). 그 값이 target인 u의 수를 더한다
        count += *on_path.get(&(prefix[hut] - target)).unwrap_or(&0);
        *on_path.get_mut(&prefix[hut]).unwrap() += 1;
        stack.push(-(hut as i64) - 1); // 아래쪽을 다 본 뒤에 꺼내지도록 먼저 넣는다
        for &next in &neighbors[hut] {
            if !visited[next] {
                visited[next] = true;
                prefix[next] = prefix[hut] + energy[next];
                stack.push(next as i64);
            }
        }
    }
    count
}
