fn solution(helpers: Vec<Vec<i32>>, close: i32, gap: i32) -> i32 {
    let mut people = helpers.clone();
    people.sort_by_key(|h| h[0]); // 오는 시각이 이른 사람부터
    let close = close as i64;
    let gap = gap as i64;
    let mut reach: i64 = 0; // 시각 0부터 reach까지는 빈 시간이 모두 gap 이하다 (reach + gap이 20억에 이를 수 있다)
    let mut best: i64 = 0; // 지금까지 본 '불러야 오는 사람' 가운데 가장 늦게 떠나는 시각
    let mut called = 0;
    let mut i = 0;
    while close - reach > gap { // 남은 시간을 비워 둘 수 없다: 누군가 더 있어야 한다
        // reach + gap 이전에 오는 사람은 지금 이어 받을 수 있다
        while i < people.len() && (people[i][0] as i64) <= reach + gap {
            let leave = people[i][1] as i64;
            if people[i][2] == 1 {
                reach = reach.max(leave); // 약속한 사람은 부르지 않아도 온다: 끝을 먼저 늘린다
            } else {
                best = best.max(leave);
            }
            i += 1;
        }
        if close - reach <= gap {
            break;
        }
        if best <= reach {
            return -1; // 누구를 불러도 reach + gap 안에 이어 받아 더 멀리 갈 수 없다
        }
        reach = best; // 이어 받을 수 있는 사람 가운데 가장 늦게 떠나는 사람을 부른다
        called += 1;
    }
    called
}
