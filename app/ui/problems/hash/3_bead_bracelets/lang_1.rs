// 언어 함정: rust.unwrap_none @ "디자인이 같은 팔찌끼리 묶었을 때"
use std::collections::HashMap;

fn solution(bracelets: Vec<String>) -> i32 {
    let mut count: HashMap<String, i32> = HashMap::new(); // 대표 키 → 그 디자인의 팔찌 수
    for beads in &bracelets {
        let flipped: String = beads.chars().rev().collect(); // 반대 방향으로 읽은 것
        let mut views: Vec<String> = Vec::new(); // 이 팔찌가 적힐 수 있는 모든 모습 (영문 소문자라 바이트 위치로 자른다)
        for start in 0..beads.len() {
            views.push(format!("{}{}", &beads[start..], &beads[..start])); // start번째 구슬부터 같은 방향으로
            views.push(format!("{}{}", &flipped[start..], &flipped[..start])); // 뒤집어서 start번째 구슬부터
        }
        let key = views.into_iter().min().unwrap(); // 사전 순으로 가장 앞선 모습을 대표로: 디자인이 같으면 키도 같다
        *count.get_mut(&key).unwrap() += 1;
    }
    *count.values().max().unwrap()
}
