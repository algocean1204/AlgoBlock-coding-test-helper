// 언어 함정: javascript.missing_key_undefined
function solution(log) {
    const count = new Map();  // 구역 → {종 → 마릿수}. 1마리 이상인 종만 둔다
    const zonesOf = new Map();  // 종 → 그 종이 1마리 이상 있는 구역 수
    const answers = [];
    for (const line of log) {
        const words = line.split(" ");
        if (words[0] === "see") {
            const zone = words[1], kind = words[2], n = Number(words[3]);
            if (!count.has(zone)) {
                count.set(zone, new Map());
            }
            const inZone = count.get(zone);
            const before = inZone.get(kind) || 0;  // 덮어쓰기 전에 지금 값을 본다
            // 종의 구역 수는 없음 → 있음, 있음 → 없음으로 바뀔 때만 달라진다
            if (before === 0 && n > 0) {
                zonesOf.set(kind, zonesOf.get(kind) + 1);
            }
            if (before > 0 && n === 0) {
                zonesOf.set(kind, zonesOf.get(kind) - 1);
            }
            if (n > 0) {
                inZone.set(kind, n);  // 더하지 않고 바꾼다
            } else {
                inZone.delete(kind);  // 0마리는 지운다: 구역의 종 수 = 안쪽 표의 크기
            }
        } else if (words[0] === "zone") {
            answers.push(count.has(words[1]) ? count.get(words[1]).size : 0);
        } else {
            answers.push(zonesOf.get(words[1]) || 0);
        }
    }
    return answers;
}
