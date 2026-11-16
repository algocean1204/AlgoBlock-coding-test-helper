// 언어 함정: javascript.recursion_depth @ "pay의 길이(축제 기간)는 1 이상 100,000 이하"
function solution(pay) {
    const n = pay.length;
    if (n === 1) {
        return pay[0];
    }
    // 길이가 10만이라 재귀 대신 반복문으로 앞에서부터 채운다
    const best = new Array(n).fill(-1);  // best[i]: 0 ~ i번째 날만 보고 골랐을 때 사례금 합의 최댓값
    best[0] = pay[0];
    best[1] = Math.max(pay[0], pay[1]);
    function go(i) {
        if (best[i] >= 0) return best[i];
        return best[i] = Math.max(go(i - 1), go(i - 2) + pay[i]);
    }
    return go(n - 1);
}
