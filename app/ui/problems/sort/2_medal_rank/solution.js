function solution(classes, medals) {
    // 반 번호(0..n-1)를 줄 세운다. 정렬 기준은 금 많은 순 → 은 많은 순 → 동 많은 순 → 이름 사전 순
    const order = classes.map((_, i) => i);
    order.sort((a, b) => {
        // 메달은 많은 쪽이 앞(내림차순)이라 b - a로 비교한다
        if (medals[a][0] !== medals[b][0]) return medals[b][0] - medals[a][0];
        if (medals[a][1] !== medals[b][1]) return medals[b][1] - medals[a][1];
        if (medals[a][2] !== medals[b][2]) return medals[b][2] - medals[a][2];
        // 이름은 사전 순(오름차순). 소문자뿐이라 < 비교가 곧 사전 순이다(localeCompare는 환경마다 달라 쓰지 않는다)
        return classes[a] < classes[b] ? -1 : 1; // 이름은 서로 다르므로 같은 경우는 없다
    });
    let answer = [];
    for (const i of order) answer.push(classes[i]);
    return answer;
}
