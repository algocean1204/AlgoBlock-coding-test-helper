// 언어 함정: rust.unwrap_none @ "제목이 같으면 같은 책입니다"
use std::collections::HashMap;

fn solution(loans: Vec<String>, k: i32) -> Vec<String> {
    let mut count: HashMap<String, i32> = HashMap::new(); // 제목마다 지금까지 빌려진 횟수
    let mut shelf: Vec<String> = Vec::new(); // 추천 서가에 꽂힌 차례대로
    for title in loans {
        let now = count.get_mut(&title).unwrap();
        *now += 1;
        if *now == k {
            // 바로 지금 k번째로 빌려졌다
            shelf.push(title);
        }
    }
    shelf
}
