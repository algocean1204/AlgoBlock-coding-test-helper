use std::collections::HashMap;

// 재귀 대신 반복문: 긴 줄 입력에서 깊어지지 않게
fn find(parent: &mut HashMap<String, String>, start: &str) -> String {
    let mut x = start.to_string();
    parent.entry(x.clone()).or_insert_with(|| x.clone());
    while parent[&x] != x {
        let grand = parent[&parent[&x]].clone();
        parent.insert(x.clone(), grand); // 경로 압축
        x = parent[&x].clone();
    }
    x
}

fn solution(cables: Vec<Vec<String>>) -> i32 {
    let mut parent: HashMap<String, String> = HashMap::new(); // 정점이 이름(문자열)이라 맵을 쓴다

    for (i, c) in cables.iter().enumerate() {
        let root_x = find(&mut parent, &c[0]);
        let root_y = find(&mut parent, &c[1]);
        if root_x == root_y {
            return i as i32 + 1; // 몇 번째 케이블인지는 1부터 센다
        }
        parent.insert(root_y, root_x);
    }
    -1
}
