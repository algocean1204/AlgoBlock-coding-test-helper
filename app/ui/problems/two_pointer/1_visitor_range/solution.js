function solution(visitors, queries) {
    // prefix[i]: 1일부터 i일까지 방문자 수의 합. prefix[0]은 아무 날도 더하지 않은 0
    const prefix = new Array(visitors.length + 1).fill(0);
    for (let i = 0; i < visitors.length; i++) {
        prefix[i + 1] = prefix[i] + visitors[i];
    }
    const answer = [];
    for (const [start, end] of queries) {
        answer.push(prefix[end] - prefix[start - 1]);
    }
    return answer;
}
