use std::collections::HashMap;

// remaining: 더 놓아야 할 자리 수, last: 바로 앞에 놓은 장르 번호(처음에는 None)
fn place(remaining: usize, last: Option<usize>, left: &mut Vec<i32>) -> i64 {
    if remaining == 0 {
        return 1;
    }
    let mut ways: i64 = 0; // 경우의 수가 i32를 넘을 수 있어 i64로 센다
    for genre in 0..left.len() {
        if left[genre] == 0 || Some(genre) == last { // 놓는 도중에 가지를 끊는다
            continue;
        }
        left[genre] -= 1;
        ways += place(remaining - 1, Some(genre), left);
        left[genre] += 1;
    }
    ways
}

fn solution(genres: Vec<String>) -> i32 {
    // 같은 장르를 개수로 묶는다: left[장르 번호] = 아직 안 놓은 팀 수
    let mut number: HashMap<String, usize> = HashMap::new();
    let mut left: Vec<i32> = Vec::new();
    for genre in &genres {
        let at = *number.entry(genre.clone()).or_insert_with(|| {
            left.push(0);
            left.len() - 1
        });
        left[at] += 1;
    }
    place(genres.len(), None, &mut left) as i32
}
