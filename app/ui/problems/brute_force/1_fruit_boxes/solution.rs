fn solution(apples: i32, pears: i32, low: i32, high: i32) -> Vec<i32> {
    let mut best_size = low;
    let mut best_left = apples + pears + 1; // 어떤 size보다도 많이 남는 값에서 시작한다
    for size in low..=high { // 상자 크기를 하나씩 대 본다(..=는 high도 포함한다)
        let left = apples % size + pears % size; // 사과와 배는 섞지 않으므로 따로 남는다
        if left <= best_left { // 같을 때도 바꾸면 더 큰 size가 남는다
            best_size = size;
            best_left = left;
        }
    }
    vec![best_size, apples / best_size + pears / best_size]
}
