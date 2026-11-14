function solution(n, roads) {
    const parent = [];
    for (let i = 0; i <= n; i++) parent.push(i);

    // 재귀 대신 반복문: 긴 줄 입력에서 스택이 넘치지 않게
    function find(x) {
        while (parent[x] !== x) {
            parent[x] = parent[parent[x]]; // 경로 압축
            x = parent[x];
        }
        return x;
    }

    const sorted = [...roads].sort((p, q) => p[2] - q[2]); // 싼 길부터 본다(수는 비교 함수가 꼭 필요)

    let total = 0;
    let paved = 0;
    for (const [a, b, cost] of sorted) {
        const rootA = find(a);
        const rootB = find(b);
        if (rootA === rootB) continue; // 이미 오갈 수 있다: 포장하면 고리가 생긴다
        parent[rootB] = rootA;
        total += cost;
        paved += 1;
    }

    if (paved < n - 1) return -1; // 다 보고도 길이 n-1개가 안 되면 묶음이 둘 이상 남았다
    return total;
}
