function solution(logs, window) {
    const answer = [];
    // 아직 가장 큰 값이 될 수 있는 기록의 번호. 배열과 앞 위치(head)로 덱을 만든다(shift()는 느리다)
    // 앞에서 뒤로 갈수록 level이 작다
    const candidates = [];
    let head = 0;
    for (let k = 0; k < logs.length; k++) {
        const time = logs[k][0];
        const level = logs[k][1];
        // 새 기록보다 작거나 같은 옛 기록은 다시는 가장 큰 값이 못 된다: 뒤에서 버린다
        while (candidates.length > head && logs[candidates[candidates.length - 1]][1] <= level) {
            candidates.pop();
        }
        candidates.push(k);
        // 창을 벗어난 오래된 기록은 앞에서 뺀다(여러 개일 수 있다). 방금 넣은 기록은 늘 창 안이라 덱이 비지 않는다
        while (logs[candidates[head]][0] <= time - window) {
            head++;
        }
        answer.push(logs[candidates[head]][1]);
    }
    return answer;
}
