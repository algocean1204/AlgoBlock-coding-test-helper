// 언어 함정: rust.unwrap_none
use std::collections::HashMap;

fn solution(presses: Vec<i32>, m: i32) -> i64 {
    let _ = m; // 조명 수는 따로 쓰지 않는다(버튼 번호가 이미 1~m이다)
    // 조명 상태를 정수 하나로 담는다: k번 조명이 켜져 있으면 (k - 1)번째 비트가 1
    let mut seen: HashMap<i32, i64> = HashMap::new(); // 상태 → 지금까지 그 상태가 나온 횟수
    seen.insert(0, 1); // 아무것도 누르지 않은 처음(모두 꺼짐)도 한 번
    let mut state: i32 = 0;
    let mut total: i64 = 0; // 토막 수는 i32를 넘을 수 있다
    for &button in &presses {
        if button == 0 {
            state = 0; // 모두 끈다
        } else {
            state ^= 1 << (button - 1); // 그 조명만 뒤집는다
        }
        // 앞서 지금과 같은 상태였던 때마다, 그 다음 버튼부터 지금 버튼까지가 제자리 토막이다
        let count = seen.get_mut(&state).unwrap();
        total += *count;
        *count += 1;
    }
    total
}
