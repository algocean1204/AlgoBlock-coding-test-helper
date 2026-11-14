function solution(baked, want, fresh) {
    const n = baked.length;
    const left = baked.slice(); // left[d]: d일에 구운 빵 가운데 아직 남은 개수
    let oldest = 0;             // 아직 남은 빵이 있을 수 있는 가장 오래된 날
    let sold = 0;
    for (let day = 0; day < n; day++) {
        oldest = Math.max(oldest, day - fresh + 1); // 기한이 지난 날의 빵은 버린다
        let need = want[day];
        while (need > 0 && oldest <= day) { // 가장 오래된 빵부터 판다
            const take = Math.min(need, left[oldest]);
            left[oldest] -= take;
            need -= take;
            sold += take;
            if (left[oldest] === 0) {
                oldest++; // 다 팔린 날은 다시 보지 않는다
            }
        }
    }
    return sold;
}
