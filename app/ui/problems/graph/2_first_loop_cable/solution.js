function solution(cables) {
    const parent = new Map(); // 정점이 이름(문자열)이라 맵을 쓴다

    // 재귀 대신 반복문: 긴 줄 입력에서 스택이 넘치지 않게
    function find(x) {
        if (!parent.has(x)) parent.set(x, x);
        while (parent.get(x) !== x) {
            parent.set(x, parent.get(parent.get(x))); // 경로 압축
            x = parent.get(x);
        }
        return x;
    }

    for (let i = 0; i < cables.length; i++) {
        const rootX = find(cables[i][0]);
        const rootY = find(cables[i][1]);
        if (rootX === rootY) {
            return i + 1; // 몇 번째 케이블인지는 1부터 센다
        }
        parent.set(rootY, rootX);
    }
    return -1;
}
