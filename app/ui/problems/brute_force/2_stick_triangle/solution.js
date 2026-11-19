function solution(sticks) {
    let count = 0;
    const n = sticks.length;
    for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
            for (let k = j + 1; k < n; k++) {
                // 작은 것부터 늘어놓으면 마지막이 가장 긴 막대다(수는 비교 함수가 꼭 필요)
                const [shortest, middle, longest] = [sticks[i], sticks[j], sticks[k]].sort((a, b) => a - b);
                if (longest < shortest + middle) {
                    count++;
                }
            }
        }
    }
    return count;
}
