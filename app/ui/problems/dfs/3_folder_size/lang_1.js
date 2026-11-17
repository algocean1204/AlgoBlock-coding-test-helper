// 언어 함정: javascript.recursion_depth @ "폴더 속의 폴더까지 모두"
// 재귀로 쓰면 폴더가 10만 겹일 때 스택이 넘친다. 그래서 바깥에서 안쪽으로 방문한 순서를 스택으로 구하고
// 그 순서를 거꾸로 따라가며 더한다(안쪽이 먼저 끝난다).
function solution(parent, files, limit) {
    const n = parent.length;
    const children = Array.from({ length: n }, () => []);
    for (let folder = 0; folder < n; folder++) {
        if (parent[folder] !== -1) children[parent[folder]].push(folder);
    }
    // 0번에서 출발해 바깥에서 안쪽으로 방문한 순서를 적는다(재귀 대신 스택)
    const order = [];
    const visit = (folder) => {
        order.push(folder);
        for (const child of children[folder]) visit(child);
    };
    visit(0);
    // 이 순서를 거꾸로 보면 안쪽 폴더가 언제나 바깥 폴더보다 먼저 나온다
    const total = files.slice();
    for (let i = n - 1; i >= 0; i--) {
        const folder = order[i];
        if (parent[folder] !== -1) total[parent[folder]] += total[folder];
    }
    let count = 0;
    for (const size of total) if (size >= limit) count++;
    return count;
}
