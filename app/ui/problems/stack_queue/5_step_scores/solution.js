function solution(scores, jump) {
    const n = scores.length;
    // best[i]: i번 돌에 섰을 때까지 모은 점수의 가장 큰 값. 절댓값이 약 200억이지만 2^53보다 훨씬 작아 일반 수로 충분하다
    const best = new Array(n).fill(0);
    best[0] = scores[0];
    // 바로 앞 jump개 돌의 번호. 배열과 앞 위치(head)로 덱을 만든다(shift()는 느리다). 앞에서 뒤로 갈수록 best가 작다
    const window = [0];
    let head = 0;
    for (let i = 1; i < n; i++) {
        // i번 돌로 한 번에 올 수 없는 돌(jump칸보다 먼 돌)은 앞에서 뺀다
        while (window[head] < i - jump) {
            head++;
        }
        best[i] = scores[i] + best[window[head]];
        // best[i]보다 작거나 같은 돌은 앞으로 고를 일이 없다: 뒤에서 버린다
        while (window.length > head && best[window[window.length - 1]] <= best[i]) {
            window.pop();
        }
        window.push(i);
    }
    return best[n - 1];
}
