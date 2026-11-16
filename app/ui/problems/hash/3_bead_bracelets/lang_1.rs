// 언어 함정: rust.unwrap_none @ "디자인이 같은 팔찌끼리 묶었을 때"
use std::collections::HashMap;

fn solution(bracelets: Vec<String>) -> i32 {
    let mut count: HashMap<String, i32> = HashMap::new(); // 대표 키 → 그 디자인의 팔찌 수
    let mut best = 0;
    for beads in &bracelets {
        let flipped: String = beads.chars().rev().collect(); // 반대 방향으로 읽은 것
        let mut key = beads.clone();
        for start in 0..beads.len() {
            // start번째 구슬부터 같은 방향으로, 그리고 뒤집어서 읽은 모습 (영문 소문자라 바이트 위치로 자른다)
            let same = format!("{}{}", &beads[start..], &beads[..start]);
            let other = format!("{}{}", &flipped[start..], &flipped[..start]);
            if same < key {
                key = same;
            }
            if other < key {
                key = other;
            }
        }
        // 사전 순으로 가장 앞선 모습을 대표로: 디자인이 같으면 키도 같다
        let now = count.get_mut(&key).unwrap();
        *now += 1;
        if *now > best {
            best = *now;
        }
    }
    best
}
