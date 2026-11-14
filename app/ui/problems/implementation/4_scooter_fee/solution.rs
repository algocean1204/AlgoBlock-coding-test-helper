use std::collections::HashMap;

// 할증 시간: 07:30 이상 09:30 미만, 17:00 이상 19:00 미만(분)
const RUSH: [(i32, i32); 2] = [(7 * 60 + 30, 9 * 60 + 30), (17 * 60, 19 * 60)];

fn to_minutes(clock: &str) -> i32 {
    clock[..2].parse::<i32>().unwrap() * 60 + clock[3..].parse::<i32>().unwrap()
}

fn ride_fee(start: i32, end: i32, per_minute: i32) -> i32 {
    // 탄 분마다 1분 요금, 할증 시간과 겹친 분은 1분 요금을 한 번 더
    let mut fee = (end - start) * per_minute;
    for &(rush_start, rush_end) in RUSH.iter() {
        let overlap = end.min(rush_end) - start.max(rush_start);
        if overlap > 0 {
            fee += overlap * per_minute;
        }
    }
    fee
}

fn solution(rides: Vec<String>, price: Vec<i32>, gap: i32) -> Vec<Vec<i32>> {
    let (unlock, per_minute, day_max) = (price[0], price[1], price[2]);

    let mut total: HashMap<&str, i32> = HashMap::new(); // 회원 → 그날 요금 합
    let mut last_end: HashMap<&str, i32> = HashMap::new(); // 회원 → 바로 앞 기록의 끝 시각(분)
    for ride in &rides {
        let words: Vec<&str> = ride.split(' ').collect();
        let member = words[0];
        let start = to_minutes(words[1]);
        let end = to_minutes(words[2]);
        let mut fee = ride_fee(start, end, per_minute);
        // 같은 회원의 바로 앞 기록이 끝난 지 gap분 이하이면 이어 탄 것: 잠금 해제 요금이 없다
        match last_end.get(member) {
            Some(&previous) if start - previous <= gap => {}
            _ => fee += unlock,
        }
        *total.entry(member).or_insert(0) += fee;
        last_end.insert(member, end);
    }

    let mut answer: Vec<Vec<i32>> = total
        .iter()
        .map(|(member, &sum)| vec![member.parse::<i32>().unwrap(), sum.min(day_max)]) // 상한은 하루 합에 한 번
        .collect();
    // 요금이 많은 회원부터, 같으면 번호가 작은 회원부터
    answer.sort_by(|a, b| b[1].cmp(&a[1]).then(a[0].cmp(&b[0])));
    answer
}
