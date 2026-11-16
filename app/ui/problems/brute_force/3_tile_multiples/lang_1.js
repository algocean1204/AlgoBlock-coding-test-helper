// 언어 함정: javascript.string_plus @ "글자 하나하나가 타일 한 장에 적힌 숫자"
function solution(tiles, m) {
    const numbers = new Set();
    const used = new Array(tiles.length).fill(false);
    // 순열 도구가 없어서 재귀로 직접 만든다: 안 쓴 타일을 하나씩 뒤에 붙여 가며 모든 순서를 본다
    function build(number, length) {
        if (length >= 2) {
            numbers.add(number); // 같은 수는 집합이 한 번만 남긴다
        }
        for (let i = 0; i < tiles.length; i++) {
            if (used[i]) continue;
            if (length === 0 && tiles[i] === "0") continue; // 맨 앞에 0 타일은 놓을 수 없다
            used[i] = true;
            build(number * 10 + tiles[i], length + 1);
            used[i] = false;
        }
    }
    build(0, 0);
    let count = 0;
    for (const x of numbers) {
        if (x % m === 0) count++;
    }
    return count;
}
