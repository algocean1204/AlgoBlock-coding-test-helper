// 재귀로 쓰면 쉼터가 5만 개 한 줄일 때 스택이 넘친다. 그래서 재귀 대신,
// '들어갈 때'와 '돌아올 때'를 스택에 따로 넣어 같은 순서를 만든다(돌아올 때는 -번호-1로 구분한다).
function solution(trails, energy, target) {
    const n = energy.length;
    const neighbors = Array.from({ length: n }, () => []);
    for (const [a, b] of trails) {
        neighbors[a].push(b); // 어느 쪽이 위쪽인지 모르므로 양쪽에 넣는다
        neighbors[b].push(a);
    }
    const prefix = new Array(n).fill(0); // prefix[v]: 0번부터 v번까지 길 위 energy의 합
    prefix[0] = energy[0];
    // 지금 경로 위의 누적 합이 몇 번씩 있는가. 0번 위(아무 쉼터도 지나지 않은 곳)의 누적 합 0을 넣어 둔다
    const onPath = new Map([[0, 1]]);
    const visited = new Array(n).fill(false);
    visited[0] = true;
    let count = 0;
    const stack = [0];
    while (stack.length > 0) {
        const top = stack.pop();
        if (top < 0) {
            const hut = -top - 1;
            onPath.set(prefix[hut], onPath.get(prefix[hut]) - 1); // 이 쉼터 아래를 다 보았다: 경로에서 뺀다
            continue;
        }
        const hut = top;
        // u부터 hut까지의 합 = prefix[hut] - (u 바로 위까지의 누적 합). 그 값이 target인 u의 수를 더한다
        count += onPath.get(prefix[hut] - target) || 0;
        onPath.set(prefix[hut], (onPath.get(prefix[hut]) || 0) + 1);
        stack.push(-hut - 1); // 아래쪽을 다 본 뒤에 꺼내지도록 먼저 넣는다
        for (const next of neighbors[hut]) {
            if (!visited[next]) {
                visited[next] = true;
                prefix[next] = prefix[hut] + energy[next];
                stack.push(next);
            }
        }
    }
    return count;
}
