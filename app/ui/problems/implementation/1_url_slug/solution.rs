use std::collections::HashSet;

fn solution(title: String, taken: Vec<String>) -> String {
    let skip = ["a", "an", "the", "of", "and"];

    // 1~2. 빈칸으로 나누고(split_whitespace는 빈 낱말을 만들지 않는다), 낱말마다 소문자로 바꿔 영문 소문자·숫자만 남긴다
    let mut words: Vec<String> = Vec::new();
    for word in title.split_whitespace() {
        let mut kept = String::new();
        for ch in word.to_lowercase().chars() {
            if ch.is_ascii_lowercase() || ch.is_ascii_digit() {
                kept.push(ch);
            }
        }
        if !kept.is_empty() {
            words.push(kept);
        }
    }

    // 3. 규칙 3의 낱말 빼기. 다 빠져 목록이 비면 빼지 않는다
    let left: Vec<String> = words.iter().filter(|word| !skip.contains(&word.as_str())).cloned().collect();
    if !left.is_empty() {
        words = left;
    }

    // 4. 낱말 단위로 이어 붙이다가 길이가 24를 넘게 되면 멈춘다
    let mut slug: String = words[0].chars().take(24).collect();
    for word in &words[1..] {
        if slug.len() + 1 + word.len() > 24 {
            break;
        }
        slug = format!("{}-{}", slug, word);
    }

    // 5. taken에 있으면 -2, -3, … 을 붙여 본다
    let used: HashSet<&String> = taken.iter().collect();
    if !used.contains(&slug) {
        return slug;
    }
    let mut number = 2;
    while used.contains(&format!("{}-{}", slug, number)) {
        number += 1;
    }
    format!("{}-{}", slug, number)
}
