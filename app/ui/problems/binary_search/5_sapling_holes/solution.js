// 모든 간격을 gap 이상으로 둘 때 심을 수 있는 묘목의 수
function planted(trees, holes, gap) {
    let count = 0;
    let last = -1e10; // 지금 보는 구덩이 바로 앞에 있는 나무(없으면 아주 먼 곳)
    let i = 0; // trees[i]: 지금 보는 구덩이 뒤에 오는 첫 큰 나무
    for (const hole of holes) {
        while (i < trees.length && trees[i] < hole) { // 구덩이보다 앞에 있는 큰 나무를 지나간다
            last = trees[i];
            i += 1;
        }
        const nextTree = i < trees.length ? trees[i] : 1e10; // 뒤에 큰 나무가 없으면 아주 먼 곳
        // 앞 나무와도, 뒤에 오는 큰 나무와도 gap 이상 떨어져야 심는다
        if (hole - last >= gap && nextTree - hole >= gap) {
            count += 1;
            last = hole;
        }
    }
    return count;
}

function solution(trees, holes, count) {
    // sort()는 글자 순이라 수는 비교 함수를 준다
    const sortedTrees = [...trees].sort((a, b) => a - b);
    const sortedHoles = [...holes].sort((a, b) => a - b);
    let left = 1;
    let right = Math.max(sortedTrees[sortedTrees.length - 1], sortedHoles[sortedHoles.length - 1])
        - Math.min(sortedTrees[0], sortedHoles[0]);
    for (let i = 0; i + 1 < sortedTrees.length; i++) { // 큰 나무끼리의 간격은 바꿀 수 없으므로 답은 이보다 클 수 없다
        right = Math.min(right, sortedTrees[i + 1] - sortedTrees[i]);
    }
    let answer = 1;
    while (left <= right) {
        const mid = Math.floor((left + right) / 2);
        if (planted(sortedTrees, sortedHoles, mid) >= count) { // 더 많이 심을 수 있으면 몇 그루를 덜 심으면 된다
            answer = mid;
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    return answer;
}
