fn solution(heights: Vec<i32>) -> Vec<i32> {
    let n = heights.len();
    let mut rests = vec![0i32; n]; // rests[j]: j번 지점에서 쉬는 등산객 수
    let mut walking: Vec<usize> = Vec::new(); // 아직 쉴 곳을 찾지 못한 등산객의 출발 지점. 위로 갈수록 높다
    for j in 0..n {
        // j번 지점이 맨 위 등산객의 출발 높이보다 낮거나 같으면, 그 등산객은 여기서 쉰다
        while let Some(&top) = walking.last() {
            if heights[top] < heights[j] {
                break;
            }
            walking.pop();
            rests[j] += 1;
        }
        walking.push(j); // j번 등산객이 걷기 시작한다
    }
    rests // 끝까지 스택에 남은 등산객은 산책길을 벗어나 어디에도 세지 않는다
}
