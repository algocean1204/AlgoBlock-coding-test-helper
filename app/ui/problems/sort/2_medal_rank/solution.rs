fn solution(classes: Vec<String>, medals: Vec<Vec<i32>>) -> Vec<String> {
    let mut rows: Vec<(i32, i32, i32, String)> = Vec::new();
    for i in 0..classes.len() {
        let (gold, silver, bronze) = (medals[i][0], medals[i][1], medals[i][2]);
        // 메달은 많은 쪽이 앞(내림차순)이라 마이너스를 붙이고, 이름은 사전 순(오름차순) 그대로 둔다
        rows.push((-gold, -silver, -bronze, classes[i].clone()));
    }
    rows.sort(); // 튜플은 앞 기준부터 비교하고, 같으면 다음 기준으로 넘어간다
    let mut answer: Vec<String> = Vec::new();
    for row in rows {
        answer.push(row.3);
    }
    answer
}
