use std::collections::VecDeque;

fn solution(logs: Vec<Vec<i32>>, window: i32) -> Vec<i32> {
    let mut answer: Vec<i32> = Vec::new();
    let mut candidates: VecDeque<(i32, i32)> = VecDeque::new(); // 아직 가장 큰 값이 될 수 있는 기록 (time, level). 앞에서 뒤로 갈수록 level이 작다
    for log in &logs {
        let time = log[0];
        let level = log[1];
        // 새 기록보다 작거나 같은 옛 기록은 다시는 가장 큰 값이 못 된다: 뒤에서 버린다
        while let Some(&(_, last_level)) = candidates.back() {
            if last_level > level {
                break;
            }
            candidates.pop_back();
        }
        candidates.push_back((time, level));
        // 창을 벗어난 오래된 기록은 앞에서 뺀다(여러 개일 수 있다). 방금 넣은 기록은 늘 창 안이라 덱이 비지 않는다
        while candidates.front().unwrap().0 <= time - window {
            candidates.pop_front();
        }
        answer.push(candidates.front().unwrap().1);
    }
    answer
}
