function solution(sticks) {
    let count = 0;
    const n = sticks.length;
    for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
            for (let k = j + 1; k < n; k++) {
                // 세 막대 중 가장 긴 것과 나머지 둘의 합을 비교한다
                const longest = Math.max(sticks[i], sticks[j], sticks[k]);
                const sum = sticks[i] + sticks[j] + sticks[k] - longest; // 가장 긴 것을 뺀 두 막대의 합
                if (longest < sum) {
                    count++;
                }
            }
        }
    }
    return count;
}
