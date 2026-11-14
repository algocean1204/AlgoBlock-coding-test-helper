function solution(profits, target) {
    // seen.get(s): 지금까지 나온 누적 합 가운데 값이 s인 것의 개수
    // 아무 날도 더하지 않은 누적 합 0을 한 번 넣어 두어야 첫째 날부터 시작하는 기간도 센다
    const seen = new Map();
    seen.set(0, 1);
    let total = 0;
    // 개수가 최대 약 50억이지만 JavaScript 수는 2^53(약 9천조)까지 정확해서 그대로 쓴다
    let count = 0;
    for (const profit of profits) {
        total += profit;
        // 앞쪽 누적 합이 total - target이었다면, 그다음 날부터 오늘까지의 합이 target이다
        // Map.get은 키가 없으면 undefined라서 || 0으로 0을 대신 쓴다
        count += seen.get(total - target) || 0;
        seen.set(total, (seen.get(total) || 0) + 1);
    }
    return count;
}
