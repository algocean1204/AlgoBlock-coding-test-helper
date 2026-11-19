const DIGITS: &str = "0123456789ABCDEF";

fn to_base(mut reading: i64, base: i64) -> String {
    // 나머지를 끝 자리부터 모은 뒤 뒤집는다
    let mut reversed_digits: Vec<char> = Vec::new();
    while reading > 0 {
        reversed_digits.push(DIGITS.as_bytes()[(reading % base) as usize] as char);
        reading /= base;
    }
    reversed_digits.iter().rev().collect()
}

fn read_base(text: &str, base: i64) -> i64 {
    // 앞자리부터 값 = 값 × base + 자리값
    let mut value: i64 = 0;
    for ch in text.chars() {
        value = value * base + DIGITS.find(ch).unwrap() as i64;
    }
    value
}

fn solution(base: i32, reading: i64) -> Vec<i64> {
    let text: Vec<char> = to_base(reading, base as i64).chars().collect();

    // 앞 자리보다 작아지는 곳에서 새 조각을 시작한다
    let mut pieces: Vec<String> = vec![text[0].to_string()];
    for i in 1..text.len() {
        if DIGITS.find(text[i]).unwrap() < DIGITS.find(text[i - 1]).unwrap() {
            pieces.push(text[i].to_string());
        } else {
            pieces.last_mut().unwrap().push(text[i]);
        }
    }
    let mut largest: i64 = 0;
    for piece in &pieces {
        let value = read_base(piece, base as i64);
        if value > largest {
            largest = value;
        }
    }
    vec![pieces.len() as i64, largest]
}
