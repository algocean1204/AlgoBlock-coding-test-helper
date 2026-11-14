// 재귀 대신 반복문: 긴 줄 입력에서 깊어지지 않게
fn find(parent: &mut Vec<usize>, mut x: usize) -> usize {
    while parent[x] != x {
        parent[x] = parent[parent[x]]; // 경로 압축
        x = parent[x];
    }
    x
}

fn solution(n: i32, roads: Vec<Vec<i32>>) -> i32 {
    let mut parent: Vec<usize> = (0..=n as usize).collect();

    let mut sorted = roads.clone();
    sorted.sort_by_key(|r| r[2]); // 싼 길부터 본다

    let mut total: i64 = 0; // 비용 합이 i32를 넘을 수 있어 i64
    let mut paved = 0;
    for r in &sorted {
        let root_a = find(&mut parent, r[0] as usize);
        let root_b = find(&mut parent, r[1] as usize);
        if root_a == root_b {
            continue; // 이미 오갈 수 있다: 포장하면 고리가 생긴다
        }
        parent[root_b] = root_a;
        total += r[2] as i64;
        paved += 1;
    }

    if paved < n - 1 {
        return -1; // 다 보고도 길이 n-1개가 안 되면 묶음이 둘 이상 남았다
    }
    total as i32
}
