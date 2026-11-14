function solution(n) {
    // n=60에서 약 4.7e15라 2^53(약 9.0e15) 안이므로 Number로 정확하다
    const ways = new Array(n + 1).fill(0);  // ways[h]: 높이가 정확히 h인 탑의 수
    ways[0] = 1;  // 아무것도 쌓지 않은 높이 0의 탑 하나
    for (let height = 1; height <= n; height++) {
        for (let block = 1; block <= 3; block++) {  // 맨 위에 놓은 블록의 높이
            if (height - block >= 0) {
                ways[height] += ways[height - block];
            }
        }
    }
    return ways[n];
}
