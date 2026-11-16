// 언어 함정: rust.i32_wrap @ "n은 1 이상 500,000,000 이하" "chargers의 원소는 1 이상 100,000 이하"
fn solution(n: i32, chargers: Vec<i32>) -> i64 {
    let fastest = *chargers.iter().min().unwrap();
    // 시간은 최대 5 x 10^13이라 i32를 넘는다. 시간과 개수 합은 i64로 둔다
    let mut left: i64 = 1;
    let product: i32 = fastest * n;
    let mut right: i64 = product as i64;
    while left < right {
        let mid = (left + right) / 2;
        let mut done: i64 = 0;
        for &minute in chargers.iter() {
            done += mid / minute as i64;
        }
        if done >= n as i64 {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    left
}
