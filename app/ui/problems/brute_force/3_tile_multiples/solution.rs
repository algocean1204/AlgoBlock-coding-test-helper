use std::collections::HashSet;

fn solution(tiles: String, m: i32) -> i32 {
    let mut numbers = HashSet::new();
    // 순열 도구가 없어서 직접 만든다: rest에서 length장을 골라 늘어놓는 모든 줄(숫자 글자뿐이라 바이트 위치로 자른다)
    fn permutations(rest: &str, length: usize) -> Vec<String> {
        if length == 0 {
            return vec![String::new()];
        }
        let mut out = Vec::new();
        for i in 0..rest.len() {
            for tail in permutations(&format!("{}{}", &rest[..i], &rest[i + 1..]), length - 1) {
                out.push(format!("{}{}", &rest[i..i + 1], tail));
            }
        }
        out
    }
    for length in 2..=tiles.len() { // 두 장 이상
        for order in permutations(&tiles, length) {
            if order.starts_with('0') { // 맨 앞에 0 타일은 놓을 수 없다
                continue;
            }
            numbers.insert(order.parse::<i32>().unwrap()); // 같은 수는 집합이 한 번만 남긴다(최대 8자리라 i32로 충분하다)
        }
    }
    let mut count = 0;
    for x in &numbers {
        if x % m == 0 {
            count += 1;
        }
    }
    count
}
