function solution(days, bookings) {
    // diff[d]: d일에 새로 늘어나는(음수면 줄어드는) 손님 수. last + 1일 = days + 1일까지 쓰므로 days + 2칸
    const diff = new Array(days + 2).fill(0);
    for (const [first, last, guests] of bookings) {
        diff[first] += guests;
        diff[last + 1] -= guests;
    }
    // 1일부터 누적하면 그날 묵는 사람 수가 된다
    let best = 0;
    let staying = 0;
    for (let day = 1; day <= days; day++) {
        staying += diff[day];
        best = Math.max(best, staying);
    }
    return best;
}
