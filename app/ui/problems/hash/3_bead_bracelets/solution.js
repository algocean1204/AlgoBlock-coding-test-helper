function solution(bracelets) {
    const count = new Map();  // 대표 키 → 그 디자인의 팔찌 수
    let best = 0;
    for (const beads of bracelets) {
        const flipped = [...beads].reverse().join("");  // 반대 방향으로 읽은 것
        let key = null;
        for (let start = 0; start < beads.length; start++) {
            // start번째 구슬부터 같은 방향으로, 그리고 뒤집어서 읽은 모습
            const same = beads.slice(start) + beads.slice(0, start);
            const other = flipped.slice(start) + flipped.slice(0, start);
            if (key === null || same < key) key = same;
            if (other < key) key = other;
        }
        // 사전 순으로 가장 앞선 모습을 대표로: 디자인이 같으면 키도 같다
        const now = (count.get(key) || 0) + 1;
        count.set(key, now);
        best = Math.max(best, now);
    }
    return best;
}
