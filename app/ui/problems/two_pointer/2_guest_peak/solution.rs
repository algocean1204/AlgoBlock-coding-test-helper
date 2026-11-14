fn solution(days: i32, bookings: Vec<Vec<i32>>) -> i32 {
    // diff[d]: d일에 새로 늘어나는(음수면 줄어드는) 손님 수. last + 1일 = days + 1일까지 쓰므로 days + 2칸
    let mut diff: Vec<i32> = vec![0; days as usize + 2];
    for booking in &bookings {
        let first = booking[0] as usize; // 인덱스로 쓰려고 usize로 바꾼다
        let last = booking[1] as usize;
        let guests = booking[2];
        diff[first] += guests;
        diff[last + 1] -= guests;
    }
    // 1일부터 누적하면 그날 묵는 사람 수가 된다
    let mut best = 0;
    let mut staying = 0;
    for day in 1..=days as usize {
        staying += diff[day];
        if staying > best {
            best = staying;
        }
    }
    best
}
