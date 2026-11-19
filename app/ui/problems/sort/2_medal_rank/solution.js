function solution(classes, medals) {
    const rows = [];
    for (let i = 0; i < classes.length; i++) {
        const [gold, silver, bronze] = medals[i];
        // 메달은 많은 쪽이 앞(내림차순)이라 마이너스를 붙이고, 이름은 사전 순(오름차순) 그대로 둔다
        rows.push([-gold, -silver, -bronze, classes[i]]);
    }
    // 앞 칸부터 비교하고, 같으면 다음 칸으로 넘어간다. 이름은 소문자뿐이라 < 비교가 곧 사전 순이다(localeCompare는 환경마다 달라 쓰지 않는다)
    rows.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2] || (a[3] < b[3] ? -1 : 1));
    const answer = [];
    for (const row of rows) answer.push(row[3]);
    return answer;
}
