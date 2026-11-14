use std::collections::HashSet;

fn solution(rows: i32, apples: Vec<Vec<i32>>, k: i32) -> Vec<i32> {
    let rows = rows as usize;
    let k = k as usize;
    let mut kinds_of: Vec<HashSet<i32>> = vec![HashSet::new(); rows + 1]; // kinds_of[줄 번호] = 그 줄의 서로 다른 무게(0번 칸은 쓰지 않는다)
    for apple in &apples {
        kinds_of[apple[0] as usize].insert(apple[1]); // 같은 무게는 한 번만
    }

    let mut answer: Vec<i32> = Vec::new();
    for row in 1..=rows {
        let mut kinds: Vec<i32> = kinds_of[row].iter().cloned().collect();
        kinds.sort_by(|a, b| b.cmp(a)); // 무거운 것부터
        // k번째 무게는 위치 k-1. 적은 무게가 k개보다 적으면 -1(사과가 없는 줄 포함)
        answer.push(if k <= kinds.len() { kinds[k - 1] } else { -1 });
    }
    answer
}
