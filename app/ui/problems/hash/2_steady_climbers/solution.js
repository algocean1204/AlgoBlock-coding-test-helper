function solution(names, days, limit) {
    const last = new Map();  // 손님 → 마지막으로 온 날
    const visits = new Map();  // 손님 → 서로 다른 날에 온 횟수
    const broken = new Set();  // 이웃한 두 날의 차이가 limit을 넘은 적이 있는 손님
    for (let i = 0; i < names.length; i++) {
        const name = names[i];
        const day = days[i];
        if (!last.has(name)) {  // 처음 온 손님
            last.set(name, day);
            visits.set(name, 1);
        } else if (day !== last.get(name)) {  // 같은 날 다시 들어온 것은 새 방문이 아니다
            if (day - last.get(name) > limit) {
                broken.add(name);
            }
            last.set(name, day);  // 이제 이 날이 마지막으로 온 날이다
            visits.set(name, visits.get(name) + 1);
        }
    }

    let steady = 0;
    for (const [name, count] of visits) {
        if (count >= 2 && !broken.has(name)) {
            steady++;
        }
    }
    return steady;
}
