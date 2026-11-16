// 언어 함정: rust.i32_wrap @ "reading은 1 이상 100,000,000,000,000(10^14) 이하"
fn solution(base: i32, reading: i64) -> Vec<i64> {
    let digits: Vec<char> = "0123456789ABCDEF".chars().collect();
    let b = base as i64;
    let value_of = |ch: char| digits.iter().position(|&d| d == ch).unwrap() as i64;

    // 나머지를 끝 자리부터 모은 뒤 뒤집는다
    let mut rest = reading;
    let mut text: Vec<char> = Vec::new();
    while rest > 0 {
        text.push(digits[(rest % b) as usize]);
        rest /= b;
    }
    text.reverse();

    // 앞 자리보다 작아지는 곳에서 새 조각을 시작한다
    let mut pieces: Vec<Vec<char>> = vec![vec![text[0]]];
    for i in 1..text.len() {
        if value_of(text[i]) < value_of(text[i - 1]) {
            pieces.push(vec![text[i]]);
        } else {
            pieces.last_mut().unwrap().push(text[i]);
        }
    }

    // 조각마다 앞자리부터 값 = 값 × base + 자리값으로 읽어 가장 큰 값을 고른다
    let mut largest: i64 = 0;
    for piece in &pieces {
        let mut value: i32 = 0;
        for &ch in piece {
            value = value * base + value_of(ch) as i32;
        }
        largest = largest.max(value as i64);
    }
    vec![pieces.len() as i64, largest]
}
