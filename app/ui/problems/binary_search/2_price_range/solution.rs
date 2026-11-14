// values에서 x 이상인 값이 처음 나오는 자리(없으면 길이)
fn first_at_least(values: &Vec<i32>, x: i32) -> usize {
    let mut left: usize = 0;
    let mut right: usize = values.len();
    while left < right {
        let mid = (left + right) / 2;
        if values[mid] >= x {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    left
}

fn solution(prices: Vec<i32>, ranges: Vec<Vec<i32>>) -> Vec<i32> {
    let mut sorted = prices.clone();
    sorted.sort();
    let mut answer: Vec<i32> = Vec::new();
    for r in ranges.iter() {
        let low = r[0];
        let high = r[1];
        let start = first_at_least(&sorted, low);
        // 가격이 정수라서 'high보다 큰 값이 처음 나오는 자리' = 'high + 1 이상이 처음 나오는 자리'
        let end = first_at_least(&sorted, high + 1);
        answer.push((end - start) as i32);
    }
    answer
}
