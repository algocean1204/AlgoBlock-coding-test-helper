fn solution(gaps: Vec<i32>, k: i32) -> i32 {
    let mut count = 0;
    let mut left = 0;
    // gaps[left]부터 gaps[right]까지의 합 = left번 역에서 right + 1번 역까지의 거리
    // k가 10억까지라 합이 10억 + 1만 정도까지 가지만 i32(약 21억) 안이다
    let mut total: i32 = 0;
    for right in 0..gaps.len() {
        total += gaps[right];
        // 거리가 모두 양수라 왼쪽을 당기면 합이 줄어든다. k 이하가 될 때까지 당긴다
        while total > k {
            total -= gaps[left];
            left += 1;
        }
        if total == k {
            count += 1;
        }
    }
    count
}
