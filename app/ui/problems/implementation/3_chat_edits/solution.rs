use std::collections::{HashMap, HashSet};

fn solution(records: Vec<String>) -> Vec<String> {
    // 첫 번째 훑기: 메시지마다 마지막 상태(보낸이, 마지막 내용, 고친 적 있는가, 지워졌는가)를 모은다
    let mut order: Vec<&str> = Vec::new();
    let mut sender: HashMap<&str, &str> = HashMap::new();
    let mut text: HashMap<&str, &str> = HashMap::new();
    let mut edited: HashSet<&str> = HashSet::new();
    let mut deleted: HashSet<&str> = HashSet::new();
    for record in &records {
        let words: Vec<&str> = record.split(' ').collect();
        let number = words[1];
        if words[0] == "SEND" {
            order.push(number);
            sender.insert(number, words[2]);
            text.insert(number, words[3]);
        } else if words[0] == "EDIT" {
            text.insert(number, words[2]);
            edited.insert(number);
        } else {
            deleted.insert(number);
        }
    }

    // 두 번째 훑기: 남은 메시지를 보낸 순서대로 보며, 바로 앞 줄과 보낸이가 같으면 그 줄에 붙인다
    let mut lines: Vec<String> = Vec::new();
    let mut line_sender = "";
    for number in order {
        if deleted.contains(number) {
            continue;
        }
        let mut shown = text[number].to_string();
        if edited.contains(number) {
            shown.push('*');
        }
        if !lines.is_empty() && line_sender == sender[number] {
            let last = lines.last_mut().unwrap();
            last.push(' ');
            last.push_str(&shown);
        } else {
            lines.push(format!("{}: {}", sender[number], shown));
            line_sender = sender[number];
        }
    }
    lines
}
