use std::collections::{HashMap, HashSet, VecDeque};

fn solution(start: String, goal: String, dictionary: Vec<String>) -> i32 {
    let words: HashSet<String> = dictionary.into_iter().collect();
    if !words.contains(&goal) {
        return -1;
    }

    // steps: start에서 낱말을 만들기까지 바꾼 횟수. 들어 있으면 이미 큐에 넣은 낱말이다
    let mut steps: HashMap<String, i32> = HashMap::new();
    steps.insert(start.clone(), 0);
    let mut queue = VecDeque::new();
    queue.push_back(start);
    while let Some(word) = queue.pop_front() {
        let here = steps[&word];
        if word == goal {
            return here;
        }
        let mut buf: Vec<u8> = word.bytes().collect();
        for i in 0..buf.len() {
            let original = buf[i];
            for ch in b'a'..=b'z' {
                if ch == original {
                    continue;
                }
                buf[i] = ch; // 한 자리만 바꾼 이웃 후보를 직접 만든다
                let candidate = String::from_utf8(buf.clone()).unwrap();
                if words.contains(&candidate) && !steps.contains_key(&candidate) {
                    steps.insert(candidate.clone(), here + 1);
                    queue.push_back(candidate);
                }
            }
            buf[i] = original;
        }
    }
    -1
}
