// day일까지(그날 포함) 이루어진 점검 수
function countUntil(schedules, day) {
    let total = 0;
    for (const [first, gap, times] of schedules) {
        if (day >= first) {  // 첫 점검 전이면 0번
            total += Math.min(times, Math.floor((day - first) / gap) + 1);  // times번을 넘지 않는다
        }
    }
    return total;
}

function solution(schedules, k) {
    let left = Infinity, right = 0;
    for (const [first, gap, times] of schedules) {
        left = Math.min(left, first);
        right = Math.max(right, first + (times - 1) * gap);
    }
    // 그날까지의 점검이 k번 이상인 가장 이른 날을 찾는다
    while (left < right) {
        const mid = Math.floor((left + right) / 2);
        if (countUntil(schedules, mid) >= k) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    return left;
}
