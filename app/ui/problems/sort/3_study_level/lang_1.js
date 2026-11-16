// 언어 함정: javascript.sort_default @ "solved의 원소는 0 이상 1,000,000,000 이하"
function solution(solved) {
    const ordered = solved.slice().sort().reverse(); // 많이 푼 회원부터. 수는 비교 함수를 줘야 글자 순이 되지 않는다
    let level = 0;
    for (let i = 0; i < ordered.length; i++) {
        // 앞에서 i+1명은 모두 ordered[i]문제 이상 풀었다.
        // 그러니 ordered[i] >= i+1이면 'i+1문제 이상 푼 회원이 i+1명 이상'이 된다
        if (ordered[i] >= i + 1) {
            level = i + 1;
        } else {
            break; // 여기서 안 되면 더 큰 x도 안 된다
        }
    }
    return level;
}
