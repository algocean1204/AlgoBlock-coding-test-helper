fn solution(books: Vec<i32>, queries: Vec<i32>) -> Vec<i32> {
    let mut answer: Vec<i32> = Vec::new();
    for &target in queries.iter() {
        // 오른쪽 끝이 -1이 될 수 있어서 부호 있는 수(i32)로 둔다
        let mut left: i32 = 0;
        let mut right: i32 = books.len() as i32 - 1;
        let mut position: i32 = -1;
        while left <= right {
            let mid = (left + right) / 2;
            if books[mid as usize] == target {
                position = mid;
                break;
            } else if books[mid as usize] < target {
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
        answer.push(position);
    }
    answer
}
