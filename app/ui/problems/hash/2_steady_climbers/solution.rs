use std::collections::{HashMap, HashSet};

fn solution(names: Vec<String>, days: Vec<i32>, limit: i32) -> i32 {
    let mut last: HashMap<&str, i32> = HashMap::new(); // 손님 → 마지막으로 온 날
    let mut visits: HashMap<&str, i32> = HashMap::new(); // 손님 → 서로 다른 날에 온 횟수
    let mut broken: HashSet<&str> = HashSet::new(); // 이웃한 두 날의 차이가 limit을 넘은 적이 있는 손님
    for i in 0..names.len() {
        let name = names[i].as_str();
        let day = days[i];
        match last.get(name) {
            None => {
                // 처음 온 손님
                last.insert(name, day);
                visits.insert(name, 1);
            }
            Some(&before) => {
                if day != before {
                    // 같은 날 다시 들어온 것은 새 방문이 아니다
                    if day - before > limit {
                        broken.insert(name);
                    }
                    last.insert(name, day); // 이제 이 날이 마지막으로 온 날이다
                    *visits.get_mut(name).unwrap() += 1;
                }
            }
        }
    }

    let mut steady = 0;
    for (name, &count) in &visits {
        if count >= 2 && !broken.contains(name) {
            steady += 1;
        }
    }
    steady
}
