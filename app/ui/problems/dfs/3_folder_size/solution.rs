// 재귀로 쓰면 폴더가 10만 겹일 때 스택이 넘칠 수 있다. 그래서 바깥에서 안쪽으로 방문한 순서를 스택으로 구하고
// 그 순서를 거꾸로 따라가며 더한다(안쪽이 먼저 끝난다).
fn solution(parent: Vec<i32>, files: Vec<i32>, limit: i32) -> i32 {
    let n = parent.len();
    let mut children: Vec<Vec<usize>> = vec![Vec::new(); n];
    for folder in 0..n {
        if parent[folder] != -1 {
            children[parent[folder] as usize].push(folder);
        }
    }
    // 0번에서 출발해 바깥에서 안쪽으로 방문한 순서를 적는다(재귀 대신 스택)
    let mut order: Vec<usize> = Vec::new();
    let mut stack: Vec<usize> = vec![0];
    while let Some(folder) = stack.pop() {
        order.push(folder);
        for &child in &children[folder] {
            stack.push(child);
        }
    }
    // 이 순서를 거꾸로 보면 안쪽 폴더가 언제나 바깥 폴더보다 먼저 나온다.
    // 전체 용량은 최대 10억이라 i32에 들어간다
    let mut total = files.clone();
    for &folder in order.iter().rev() {
        if parent[folder] != -1 {
            let up = parent[folder] as usize;
            total[up] += total[folder];
        }
    }
    total.iter().filter(|&&size| size >= limit).count() as i32
}
