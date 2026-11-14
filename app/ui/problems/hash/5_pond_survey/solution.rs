use std::collections::HashMap;

fn solution(log: Vec<String>) -> Vec<i32> {
    let mut count: HashMap<&str, HashMap<&str, i32>> = HashMap::new(); // 구역 → {종 → 마릿수}. 1마리 이상인 종만 둔다
    let mut zones_of: HashMap<&str, i32> = HashMap::new(); // 종 → 그 종이 1마리 이상 있는 구역 수
    let mut answers: Vec<i32> = Vec::new();
    for line in &log {
        let words: Vec<&str> = line.split(' ').collect();
        if words[0] == "see" {
            let (zone, kind) = (words[1], words[2]);
            let n: i32 = words[3].parse().unwrap();
            let in_zone = count.entry(zone).or_insert_with(HashMap::new);
            let before = *in_zone.get(kind).unwrap_or(&0); // 덮어쓰기 전에 지금 값을 본다
            // 종의 구역 수는 없음 → 있음, 있음 → 없음으로 바뀔 때만 달라진다
            if before == 0 && n > 0 {
                *zones_of.entry(kind).or_insert(0) += 1;
            }
            if before > 0 && n == 0 {
                *zones_of.get_mut(kind).unwrap() -= 1;
            }
            if n > 0 {
                in_zone.insert(kind, n); // 더하지 않고 바꾼다
            } else {
                in_zone.remove(kind); // 0마리는 지운다: 구역의 종 수 = 안쪽 표의 크기
            }
        } else if words[0] == "zone" {
            answers.push(count.get(words[1]).map_or(0, |in_zone| in_zone.len() as i32));
        } else {
            answers.push(*zones_of.get(words[1]).unwrap_or(&0));
        }
    }
    answers
}
