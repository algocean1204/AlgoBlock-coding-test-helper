// day일까지(그날 포함) 이루어진 점검 수. 모두 400억 번까지라 i64로 센다
fn count_until(schedules: &Vec<Vec<i32>>, day: i64) -> i64 {
    let mut total: i64 = 0;
    for s in schedules {
        let (first, gap, times) = (s[0] as i64, s[1] as i64, s[2] as i64);
        if day >= first {
            // 첫 점검 전이면 0번, times번을 넘지 않는다
            total += std::cmp::min(times, (day - first) / gap + 1);
        }
    }
    total
}

fn solution(schedules: Vec<Vec<i32>>, k: i64) -> i64 {
    let mut left = i64::MAX;
    let mut right: i64 = 0;
    for s in &schedules {
        let (first, gap, times) = (s[0] as i64, s[1] as i64, s[2] as i64);
        left = left.min(first);
        right = right.max(first + (times - 1) * gap);
    }
    // 그날까지의 점검이 k번 이상인 가장 이른 날을 찾는다
    while left < right {
        let mid = (left + right) / 2;
        if count_until(&schedules, mid) >= k {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    left
}
