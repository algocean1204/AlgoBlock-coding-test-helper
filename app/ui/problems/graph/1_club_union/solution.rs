// find를 재귀로 쓰면 긴 줄 입력에서 깊어지므로 반복문으로 쓴다
fn find(parent: &mut Vec<usize>, mut x: usize) -> usize {
    while parent[x] != x {
        parent[x] = parent[parent[x]]; // 경로 압축: 한 칸 위를 건너뛰어 대표에 가깝게 고쳐 둔다
        x = parent[x];
    }
    x
}

fn solution(n: i32, merges: Vec<Vec<i32>>) -> i32 {
    let mut parent: Vec<usize> = (0..=n as usize).collect();

    let mut groups = n;
    for m in &merges {
        let root_a = find(&mut parent, m[0] as usize);
        let root_b = find(&mut parent, m[1] as usize);
        if root_a != root_b {
            parent[root_b] = root_a;
            groups -= 1;
        }
    }
    groups
}
