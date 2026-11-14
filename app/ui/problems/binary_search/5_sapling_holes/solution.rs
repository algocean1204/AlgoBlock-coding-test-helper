// 모든 간격을 gap 이상으로 둘 때 심을 수 있는 묘목의 수
fn planted(trees: &Vec<i32>, holes: &Vec<i32>, gap: i32) -> i32 {
    let mut count = 0;
    let mut last: i32 = -1_000_000_000; // 지금 보는 구덩이 바로 앞에 있는 나무(없으면 아주 먼 곳)
    let mut i = 0; // trees[i]: 지금 보는 구덩이 뒤에 오는 첫 큰 나무
    for &hole in holes.iter() {
        while i < trees.len() && trees[i] < hole {
            // 구덩이보다 앞에 있는 큰 나무를 지나간다
            last = trees[i];
            i += 1;
        }
        let next_tree = if i < trees.len() { trees[i] } else { 2_000_000_000 }; // 뒤에 큰 나무가 없으면 아주 먼 곳
        // 앞 나무와도, 뒤에 오는 큰 나무와도 gap 이상 떨어져야 심는다
        if hole - last >= gap && next_tree - hole >= gap {
            count += 1;
            last = hole;
        }
    }
    count
}

fn solution(trees: Vec<i32>, holes: Vec<i32>, count: i32) -> i32 {
    let mut trees = trees.clone();
    let mut holes = holes.clone();
    trees.sort();
    holes.sort();
    let mut left: i32 = 1;
    let mut right: i32 = trees[trees.len() - 1].max(holes[holes.len() - 1]) - trees[0].min(holes[0]);
    for i in 0..trees.len() - 1 {
        // 큰 나무끼리의 간격은 바꿀 수 없으므로 답은 이보다 클 수 없다
        right = right.min(trees[i + 1] - trees[i]);
    }
    let mut answer: i32 = 1;
    while left <= right {
        let mid = left + (right - left) / 2;
        if planted(&trees, &holes, mid) >= count {
            // 더 많이 심을 수 있으면 몇 그루를 덜 심으면 된다
            answer = mid;
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    answer
}
