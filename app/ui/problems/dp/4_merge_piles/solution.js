function solution(piles) {
    const n = piles.length;
    const prefix = new Array(n + 1).fill(0);  // prefix[i]: piles[0] ~ piles[i - 1]의 합
    for (let i = 0; i < n; i++) {
        prefix[i + 1] = prefix[i] + piles[i];
    }
    const cost = [];  // cost[i][j]: i ~ j번째 더미를 한 더미로 만드는 최소 시간
    for (let i = 0; i < n; i++) {
        cost.push(new Array(n).fill(0));
    }
    for (let length = 2; length <= n; length++) {  // 짧은 구간부터 채운다
        for (let i = 0; i + length - 1 < n; i++) {
            const j = i + length - 1;
            let best = Infinity;
            for (let k = i; k < j; k++) {  // 마지막에 [i, k] 더미와 [k + 1, j] 더미를 합친다
                best = Math.min(best, cost[i][k] + cost[k + 1][j]);
            }
            cost[i][j] = best + prefix[j + 1] - prefix[i];  // 마지막 합치기에 드는 시간 = 구간 전체의 자루 수
        }
    }
    return cost[0][n - 1];
}
