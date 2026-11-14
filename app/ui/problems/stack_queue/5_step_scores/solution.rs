use std::collections::VecDeque;

fn solution(scores: Vec<i32>, jump: i32) -> i64 {
    let n = scores.len();
    let jump = jump as usize;
    let mut best = vec![0i64; n]; // best[i]: i번 돌에 섰을 때까지 모은 점수의 가장 큰 값. 합이 i32를 넘을 수 있어 i64
    best[0] = scores[0] as i64;
    let mut window: VecDeque<usize> = VecDeque::new(); // 바로 앞 jump개 돌의 번호. 앞에서 뒤로 갈수록 best가 작다
    window.push_back(0);
    for i in 1..n {
        // i번 돌로 한 번에 올 수 없는 돌(jump칸보다 먼 돌)은 앞에서 뺀다
        while *window.front().unwrap() + jump < i {
            window.pop_front();
        }
        best[i] = scores[i] as i64 + best[*window.front().unwrap()];
        // best[i]보다 작거나 같은 돌은 앞으로 고를 일이 없다: 뒤에서 버린다
        while let Some(&last) = window.back() {
            if best[last] > best[i] {
                break;
            }
            window.pop_back();
        }
        window.push_back(i);
    }
    best[n - 1]
}
