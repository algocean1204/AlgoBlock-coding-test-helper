// 언어 함정: javascript.fill_shared
function solution(items, capacity) {
    const n = items.length;
    // best[i][w]: 앞의 i개 물건만 보고, 무게 합이 w 이하가 되도록 골랐을 때 쓸모 점수 합의 최댓값
    const best = new Array(n + 1).fill(new Array(capacity + 1).fill(0));
    for (let i = 1; i <= n; i++) {
        const [weight, value] = items[i - 1];
        for (let w = 0; w <= capacity; w++) {
            best[i][w] = best[i - 1][w];  // i번째 물건을 넣지 않는다
            if (weight <= w) {  // i번째 물건을 넣는다: 나머지 무게 w - weight는 앞의 물건들로 채운다
                best[i][w] = Math.max(best[i][w], best[i - 1][w - weight] + value);
            }
        }
    }
    return best[n][capacity];
}
