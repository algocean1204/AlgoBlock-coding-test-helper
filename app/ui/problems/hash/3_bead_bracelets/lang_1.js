// 언어 함정: javascript.missing_key_undefined
function solution(bracelets) {
    const count = new Map();  // 대표 키 → 그 디자인의 팔찌 수
    for (const beads of bracelets) {
        const flipped = [...beads].reverse().join("");  // 반대 방향으로 읽은 것
        const views = [];  // 이 팔찌가 적힐 수 있는 모든 모습
        for (let start = 0; start < beads.length; start++) {
            views.push(beads.slice(start) + beads.slice(0, start));  // start번째 구슬부터 같은 방향으로
            views.push(flipped.slice(start) + flipped.slice(0, start));  // 뒤집어서 start번째 구슬부터
        }
        const key = views.reduce((least, view) => (view < least ? view : least));  // 사전 순으로 가장 앞선 모습을 대표로: 디자인이 같으면 키도 같다
        count.set(key, count.get(key) + 1);
    }
    let best = 0;
    for (const n of count.values()) best = Math.max(best, n);
    return best;
}
