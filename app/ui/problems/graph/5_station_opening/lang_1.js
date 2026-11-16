// 언어 함정: javascript.fill_shared
function solution(n, tracks, queries) {
    const INF = 1000000000; // 가장 긴 최단 시간(299,000)보다 크다. 자바스크립트 수는 2^53까지 정확해 두 번 더해도 안전하다
    const dist = new Array(n + 1).fill(new Array(n + 1).fill(INF));
    for (let s = 1; s <= n; s++) dist[s][s] = 0;
    for (const [a, b, minutes] of tracks) {
        if (minutes < dist[a][b]) { // 같은 두 역 사이 선로가 여럿이면 짧은 것만 남긴다
            dist[a][b] = minutes;
            dist[b][a] = minutes;
        }
    }

    const asked = []; // asked[k]: k번 역까지 열렸을 때를 묻는 질문의 번호들
    for (let i = 0; i <= n; i++) asked.push([]);
    queries.forEach(([k], index) => asked[k].push(index));

    const answer = new Array(queries.length).fill(0);
    for (let k = 1; k <= n; k++) {
        // 플로이드: k번 역을 거쳐 가는 길로 모든 두 역 사이 거리를 고친다(아직 닫힌 역까지의 거리도 고쳐 둔다)
        for (let i = 1; i <= n; i++) {
            for (let j = 1; j <= n; j++) {
                if (dist[i][k] + dist[k][j] < dist[i][j]) {
                    dist[i][j] = dist[i][k] + dist[k][j];
                }
            }
        }
        // 이제 dist[a][b]는 1~k번 역만 거쳐 가는 가장 짧은 시간이다
        for (const index of asked[k]) {
            const d = dist[queries[index][1]][queries[index][2]];
            answer[index] = d >= INF ? -1 : d;
        }
    }
    return answer;
}
