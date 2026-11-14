fn solution(classes: Vec<String>, medals: Vec<Vec<i32>>) -> Vec<String> {
    // 반 번호(0..n-1)를 줄 세운다. 정렬 기준은 금 많은 순 → 은 많은 순 → 동 많은 순 → 이름 사전 순
    let mut order: Vec<usize> = (0..classes.len()).collect();
    order.sort_by(|&a, &b| {
        // 메달은 많은 쪽이 앞(내림차순)이라 b와 a의 자리를 바꿔 비교한다
        medals[b][0]
            .cmp(&medals[a][0])
            .then(medals[b][1].cmp(&medals[a][1]))
            .then(medals[b][2].cmp(&medals[a][2]))
            .then(classes[a].cmp(&classes[b])) // 이름은 사전 순(오름차순)
    });
    let mut answer: Vec<String> = Vec::new();
    for i in order {
        answer.push(classes[i].clone());
    }
    answer
}
