function solution(n, merges) {
    const parent = [];
    for (let i = 0; i <= n; i++) parent.push(i);

    // find를 재귀로 쓰면 긴 줄 입력에서 스택이 넘치므로 반복문으로 쓴다
    function find(x) {
        while (parent[x] !== x) {
            parent[x] = parent[parent[x]]; // 경로 압축: 한 칸 위를 건너뛰어 대표에 가깝게 고쳐 둔다
            x = parent[x];
        }
        return x;
    }

    let groups = n;
    for (const [a, b] of merges) {
        const rootA = find(a);
        const rootB = find(b);
        if (rootA !== rootB) {
            parent[rootB] = rootA;
            groups -= 1;
        }
    }
    return groups;
}
