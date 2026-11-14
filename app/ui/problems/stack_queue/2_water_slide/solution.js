function solution(arrive, ride, gap, cap) {
    // 미끄럼틀 안에 있는 사람이 벗어나는 시각. 먼저 출발한 사람이 앞.
    // 배열의 shift()는 느리므로 맨 앞 자리(head)를 따로 들고 다닌다
    const sliding = [];
    let head = 0;
    let nextPerson = 0;    // 줄의 맨 앞 사람 번호
    let lastStart = -1;    // 바로 앞사람이 출발한 시각(아직 아무도 출발하지 않았으면 -1)
    let total = 0;
    let time = 0;
    while (nextPerson < arrive.length) {
        while (head < sliding.length && sliding[head] === time) { // 먼저 벗어난다
            head++;
        }
        const arrived = arrive[nextPerson] <= time;
        const room = sliding.length - head < cap;
        const gapPassed = lastStart === -1 || time - lastStart >= gap;
        if (arrived && room && gapPassed) { // 그다음 맨 앞 사람 한 명이 출발한다
            sliding.push(time + ride);
            total += time - arrive[nextPerson];
            lastStart = time;
            nextPerson++;
        }
        time++;
    }
    return total;
}
