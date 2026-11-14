function solution(n, cables, start, offline) {
    const neighbors = Array.from({ length: n + 1 }, () => []);
    for (const [a, b] of cables) {
        neighbors[a].push(b); // 케이블은 양쪽 방향이다
        neighbors[b].push(a);
    }
    const off = new Array(n + 1).fill(false); // off[v]: v번 서버가 꺼져 있는가
    for (const server of offline) off[server] = true;

    // minute[v]: v번 서버가 파일을 받는 시각. -1은 아직(또는 끝내) 받지 못한 서버
    const minute = new Array(n + 1).fill(-1);
    minute[start] = 0;
    const queue = [start];
    let head = 0; // shift()는 느릴 수 있어 읽는 위치로 큐를 흉내 낸다
    while (head < queue.length) {
        const server = queue[head++];
        for (const next of neighbors[server]) {
            if (minute[next] === -1 && !off[next]) { // 꺼진 서버는 받지도 보내지도 않는다
                minute[next] = minute[server] + 1;
                queue.push(next);
            }
        }
    }
    let latest = -1; // start번 서버가 0분이라 받지 못한 서버(-1)는 가장 큰 값이 되지 않는다
    for (const v of minute) latest = Math.max(latest, v);
    return [latest, minute.filter(v => v === latest).length];
}
