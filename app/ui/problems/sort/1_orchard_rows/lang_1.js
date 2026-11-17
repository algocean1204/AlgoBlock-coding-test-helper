// 언어 함정: javascript.sort_default @ "무게는 1 이상 400 이하"
function solution(rows, apples, k) {
    const kindsOf = [];  // kindsOf[줄 번호] = 그 줄의 서로 다른 무게(0번 칸은 쓰지 않는다)
    for (let row = 0; row <= rows; row++) {
        kindsOf.push(new Set());
    }
    for (const [row, weight] of apples) {
        kindsOf[row].add(weight);  // 같은 무게는 한 번만
    }

    const answer = [];
    for (let row = 1; row <= rows; row++) {
        const kinds = [...kindsOf[row]].sort().reverse();  // 무거운 것부터(숫자로 비교한다)
        // k번째 무게는 위치 k-1. 적은 무게가 k개보다 적으면 -1(사과가 없는 줄 포함)
        answer.push(k <= kinds.length ? kinds[k - 1] : -1);
    }
    return answer;
}
