function solution(logs) {
    let events = [];
    for (const [login, logout] of logs) {
        events.push([login, 1]);   // 접속: 인원 +1
        events.push([logout, -1]); // 끊음: 인원 -1
    }
    // 시각 순으로 정렬한다. 같은 초면 -1(끊음)이 +1(접속)보다 앞에 온다.
    // logout초에는 이미 접속해 있지 않으므로, 같은 초의 접속보다 먼저 빼 주어야 한다.
    events.sort((a, b) => {
        if (a[0] !== b[0]) return a[0] - b[0]; // 시각 오름차순
        return a[1] - b[1]; // 같은 시각이면 -1이 +1보다 앞
    });

    let inside = 0;  // 지금 접속해 있는 인원
    let most = 0;    // 지금까지 본 가장 많은 인원
    let seconds = 0; // 인원이 most였던 초의 개수
    for (let i = 0; i < events.length - 1; i++) {
        const [time, change] = events[i];
        inside += change;
        const length = events[i + 1][0] - time; // 다음 사건 전까지 inside명이 이어진다(같은 초의 사건 사이는 0초)
        // 같은 초 안에서 잠깐 생기는 중간 인원은 length가 0이라 seconds에 더해지지 않는다.
        // 끊음을 먼저 빼고 접속을 나중에 더하므로, 중간 인원이 그 초의 최종 인원보다 커지는 일도 없다.
        if (inside > most) {
            most = inside;
            seconds = length; // 최댓값이 바뀌었으니 처음부터 다시 센다
        } else if (inside === most) {
            seconds += length;
        }
    }
    return [most, seconds];
}
