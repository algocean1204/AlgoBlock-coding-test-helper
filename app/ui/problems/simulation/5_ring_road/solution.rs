use std::collections::HashMap;

fn solution(road: String, t: i64) -> i64 {
    let n = road.len();
    let mut first_seen: HashMap<Vec<u8>, usize> = HashMap::new(); // 도로 모습 → 그 모습이 처음 나온 시각(초)
    let mut passed: Vec<i64> = vec![0]; // passed[s] = 처음 s초 동안 결승선을 지나간 횟수
    let mut state: Vec<u8> = road.into_bytes();
    let mut second: usize = 0;
    while (second as i64) < t && !first_seen.contains_key(&state) {
        first_seen.insert(state.clone(), second);
        let crossed = if state[n - 1] == b'>' && state[0] == b'.' { 1 } else { 0 };
        // 1초가 시작될 때의 state만 보고 새 도로 new_road에 적는다
        let mut new_road = vec![b'.'; n];
        for i in 0..n {
            if state[i] == b'>' {
                let front = (i + 1) % n;
                if state[front] == b'.' {
                    new_road[front] = b'>';
                } else {
                    new_road[i] = b'>';
                }
            }
        }
        state = new_road;
        second += 1;
        let last = passed[passed.len() - 1];
        passed.push(last + crossed);
    }
    if second as i64 == t {
        return passed[t as usize];
    }
    // second초의 모습이 start초에 이미 나왔다: start초부터 cycle초마다 같은 흐름이 되풀이된다
    let start = first_seen[&state];
    let cycle = (second - start) as i64;
    let per_cycle = passed[second] - passed[start];
    let full = (t - start as i64) / cycle;
    let rest = ((t - start as i64) % cycle) as usize;
    passed[start] + full * per_cycle + (passed[start + rest] - passed[start])
}
