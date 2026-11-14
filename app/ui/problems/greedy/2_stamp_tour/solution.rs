use std::collections::HashMap;

fn solution(kinds: Vec<String>, minutes: Vec<i32>, time: i32) -> i32 {
    // 모양마다 그 도장을 받는 가장 짧은 시간만 남긴다(같은 모양은 한 칸만 채우므로)
    let mut shortest: HashMap<String, i32> = HashMap::new();
    for i in 0..kinds.len() {
        let entry = shortest.entry(kinds[i].clone()).or_insert(minutes[i]);
        if minutes[i] < *entry {
            *entry = minutes[i];
        }
    }
    let mut sorted: Vec<i32> = shortest.values().cloned().collect();
    sorted.sort(); // 짧은 것부터

    let mut used: i64 = 0; // 지금까지 쓴 시간
    let mut filled = 0; // 채운 칸 수
    for minute in sorted {
        if used + minute as i64 > time as i64 {
            break; // 이것이 안 들어가면 뒤의 더 긴 것도 안 들어간다
        }
        used += minute as i64;
        filled += 1;
    }
    filled
}
