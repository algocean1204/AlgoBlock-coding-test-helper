// station까지 왔을 때, 여기서 n - 1번 역까지 이어 갈 수 있는 길의 수
fn count_from(station: usize, rails: &Vec<Vec<i32>>, on_route: &mut Vec<bool>) -> i32 {
    let n = rails.len();
    if station == n - 1 {
        return 1; // 도착: 길 하나가 완성되고 여기서 끝난다
    }
    let mut routes = 0;
    for next in 0..n {
        if rails[station][next] == 1 && !on_route[next] {
            on_route[next] = true; // 들어갈 때 표시한다
            routes += count_from(next, rails, on_route);
            on_route[next] = false; // 돌아올 때 지운다: 다른 갈래에서 이 역을 다시 쓸 수 있게
        }
    }
    routes
}

fn solution(rails: Vec<Vec<i32>>) -> i32 {
    let n = rails.len();
    let mut on_route = vec![false; n]; // 지금 만들고 있는 길 위에 있는 역
    on_route[0] = true; // 출발역도 길 위에 있다
    count_from(0, &rails, &mut on_route)
}
