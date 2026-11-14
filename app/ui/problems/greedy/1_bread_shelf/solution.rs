fn solution(baked: Vec<i32>, want: Vec<i32>, fresh: i32) -> i32 {
    let n = baked.len() as i32;
    let mut left = baked.clone(); // left[d]: d일에 구운 빵 가운데 아직 남은 개수
    let mut oldest: i32 = 0; // 아직 남은 빵이 있을 수 있는 가장 오래된 날
    let mut sold = 0;
    for day in 0..n {
        oldest = oldest.max(day - fresh + 1); // 기한이 지난 날의 빵은 버린다
        let mut need = want[day as usize];
        while need > 0 && oldest <= day { // 가장 오래된 빵부터 판다
            let d = oldest as usize;
            let take = need.min(left[d]);
            left[d] -= take;
            need -= take;
            sold += take;
            if left[d] == 0 {
                oldest += 1; // 다 팔린 날은 다시 보지 않는다
            }
        }
    }
    sold
}
