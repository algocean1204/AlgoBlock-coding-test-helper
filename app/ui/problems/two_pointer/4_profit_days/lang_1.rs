// 언어 함정: rust.i32_wrap @ "profits의 길이는 1 이상 100,000 이하"
use std::collections::HashMap;

fn solution(profits: Vec<i32>, target: i32) -> i64 {
    // seen[&s]: 지금까지 나온 누적 합 가운데 값이 s인 것의 개수
    // 아무 날도 더하지 않은 누적 합 0을 한 번 넣어 두어야 첫째 날부터 시작하는 기간도 센다
    let mut seen: HashMap<i64, i64> = HashMap::new();
    seen.insert(0, 1);
    let mut total: i64 = 0;
    // 개수가 최대 약 50억이라 i32가 넘친다. i64를 쓴다
    let mut count: i32 = 0;
    for profit in profits {
        total += profit as i64;
        // 앞쪽 누적 합이 total - target이었다면, 그다음 날부터 오늘까지의 합이 target이다
        // get은 Option을 돌려준다. 없으면 0으로 본다
        count += *seen.get(&(total - target as i64)).unwrap_or(&0) as i32;
        *seen.entry(total).or_insert(0) += 1;
    }
    count as i64
}
