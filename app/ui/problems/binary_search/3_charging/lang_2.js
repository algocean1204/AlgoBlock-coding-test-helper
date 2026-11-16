// 언어 함정: javascript.float_division
function solution(n, chargers) {
    // 시간은 최대 5 x 10^13, 개수 합은 최대 2.5 x 10^13이라 int는 넘지만 JavaScript의 수(2^53 약 9 x 10^15)에는 든다
    let left = 1;
    let right = Math.min(...chargers) * n;
    while (left < right) {
        // (left + right) >> 1 은 32비트로 잘려 무한 반복이 되니, 나눗셈과 내림을 쓴다
        const mid = Math.floor((left + right) / 2);
        let done = 0;
        for (const minute of chargers) {
            done += mid / minute;
        }
        if (done >= n) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    return left;
}
