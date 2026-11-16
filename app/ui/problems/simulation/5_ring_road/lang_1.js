// 언어 함정: javascript.float_division
function solution(road, t) {
    const n = road.length;
    const firstSeen = new Map(); // 도로 모습 → 그 모습이 처음 나온 시각(초)
    const passed = [0];          // passed[s] = 처음 s초 동안 결승선을 지나간 횟수
    let state = road;
    let second = 0;
    while (second < t && !firstSeen.has(state)) {
        firstSeen.set(state, second);
        const crossed = (state[n - 1] === '>' && state[0] === '.') ? 1 : 0;
        // 1초가 시작될 때의 state만 보고 새 도로 newRoad에 적는다
        const newRoad = new Array(n).fill('.');
        for (let i = 0; i < n; i++) {
            if (state[i] === '>') {
                const front = (i + 1) % n;
                if (state[front] === '.') newRoad[front] = '>';
                else newRoad[i] = '>';
            }
        }
        state = newRoad.join('');
        second++;
        passed.push(passed[passed.length - 1] + crossed);
    }
    if (second === t) return passed[t];
    // second초의 모습이 start초에 이미 나왔다: start초부터 cycle초마다 같은 흐름이 되풀이된다
    const start = firstSeen.get(state);
    const cycle = second - start;
    const perCycle = passed[second] - passed[start];
    const full = (t - start) / cycle; // t는 10^12까지라 2^53 안이어서 Number로 충분하다
    const rest = (t - start) % cycle;
    return passed[start] + full * perCycle + (passed[start + rest] - passed[start]);
}
