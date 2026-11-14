use std::collections::HashSet;

// 순열 도구가 없어서 재귀로 직접 만든다: 안 쓴 타일을 하나씩 뒤에 붙여 가며 모든 순서를 본다
fn build(tiles: &[u8], used: &mut Vec<bool>, number: i32, length: usize, numbers: &mut HashSet<i32>) {
    if length >= 2 {
        numbers.insert(number); // 같은 수는 집합이 한 번만 남긴다
    }
    for i in 0..tiles.len() {
        if used[i] {
            continue;
        }
        if length == 0 && tiles[i] == b'0' {
            continue; // 맨 앞에 0 타일은 놓을 수 없다
        }
        used[i] = true;
        // 최대 8자리라 i32로 충분하다
        build(tiles, used, number * 10 + (tiles[i] - b'0') as i32, length + 1, numbers);
        used[i] = false;
    }
}

fn solution(tiles: String, m: i32) -> i32 {
    let mut numbers = HashSet::new();
    let mut used = vec![false; tiles.len()];
    build(tiles.as_bytes(), &mut used, 0, 0, &mut numbers);
    numbers.iter().filter(|&&x| x % m == 0).count() as i32
}
