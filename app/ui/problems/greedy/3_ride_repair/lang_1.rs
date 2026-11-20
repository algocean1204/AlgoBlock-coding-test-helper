// 언어 함정: rust.i32_wrap @ "기다림의 합"
fn solution(fix: Vec<i32>, line: Vec<i32>, walk: i32) -> i64 {
    // a 다음에 b를 고치면 b의 손님이 (fix[a] + walk) × line[b]만큼 더 기다리고,
    // b 다음에 a를 고치면 a의 손님이 (fix[b] + walk) × line[a]만큼 더 기다린다 → 작은 쪽 차례가 앞
    let compare = |&a: &usize, &b: &usize| {
        let ab = (fix[a] + walk) as i64 * line[b] as i64;
        let ba = (fix[b] + walk) as i64 * line[a] as i64;
        ab.cmp(&ba)
    };

    let n = fix.len();
    let mut order: Vec<usize> = (0..n).collect();
    order.sort_by(compare);

    let mut now: i64 = 0; // 지금 시각
    let mut total: i32 = 0; // 기다림의 합
    for (k, &ride) in order.iter().enumerate() {
        if k > 0 {
            now += walk as i64; // 다음 놀이기구까지 걸어간다(첫 놀이기구는 걷지 않는다)
        }
        now += fix[ride] as i64; // 이 놀이기구를 다 고친 시각
        total += now as i32 * line[ride];
    }
    total.into()
}
