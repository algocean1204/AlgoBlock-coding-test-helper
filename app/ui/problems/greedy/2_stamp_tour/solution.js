function solution(kinds, minutes, time) {
    // 모양마다 그 도장을 받는 가장 짧은 시간만 남긴다(같은 모양은 한 칸만 채우므로)
    const shortest = new Map();
    for (let i = 0; i < kinds.length; i++) {
        const before = shortest.get(kinds[i]);
        if (before === undefined || minutes[i] < before) {
            shortest.set(kinds[i], minutes[i]);
        }
    }
    const sorted = [...shortest.values()].sort((a, b) => a - b);  // 짧은 것부터 (sort()는 글자 순이라 수는 비교 함수를 준다)

    let used = 0;  // 지금까지 쓴 시간
    let filled = 0;  // 채운 칸 수
    for (const minute of sorted) {
        if (used + minute > time) {
            break;  // 이것이 안 들어가면 뒤의 더 긴 것도 안 들어간다
        }
        used += minute;
        filled++;
    }
    return filled;
}
