function solution(tiles, m) {
    const numbers = new Set();
    // 순열 도구가 없어서 직접 만든다: rest에서 length장을 골라 늘어놓는 모든 줄
    const permutations = (rest, length) => {
        if (length === 0) return [""];
        const out = [];
        for (let i = 0; i < rest.length; i++) {
            for (const tail of permutations(rest.slice(0, i) + rest.slice(i + 1), length - 1)) {
                out.push(rest[i] + tail);
            }
        }
        return out;
    };
    for (let length = 2; length <= tiles.length; length++) { // 두 장 이상
        for (const order of permutations(tiles, length)) {
            if (order[0] === "0") continue; // 맨 앞에 0 타일은 놓을 수 없다
            let value = 0;
            for (const ch of order) value = value * 10 + Number(ch);
            numbers.add(value); // 같은 수는 집합이 한 번만 남긴다
        }
    }
    let count = 0;
    for (const x of numbers) {
        if (x % m === 0) count++;
    }
    return count;
}
