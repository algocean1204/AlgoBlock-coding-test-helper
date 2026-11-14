// 할증 시간: 07:30 이상 09:30 미만, 17:00 이상 19:00 미만(분)
const RUSH = [[7 * 60 + 30, 9 * 60 + 30], [17 * 60, 19 * 60]];

function toMinutes(clock) {
    return Number(clock.slice(0, 2)) * 60 + Number(clock.slice(3));
}

function rideFee(start, end, perMinute) {
    // 탄 분마다 1분 요금, 할증 시간과 겹친 분은 1분 요금을 한 번 더
    let fee = (end - start) * perMinute;
    for (const [rushStart, rushEnd] of RUSH) {
        const overlap = Math.min(end, rushEnd) - Math.max(start, rushStart);
        if (overlap > 0) {
            fee += overlap * perMinute;
        }
    }
    return fee;
}

function solution(rides, price, gap) {
    const [unlock, perMinute, dayMax] = price;

    const total = new Map();  // 회원 → 그날 요금 합
    const lastEnd = new Map();  // 회원 → 바로 앞 기록의 끝 시각(분)
    for (const ride of rides) {
        const [member, startClock, endClock] = ride.split(" ");
        const start = toMinutes(startClock);
        const end = toMinutes(endClock);
        let fee = rideFee(start, end, perMinute);
        // 같은 회원의 바로 앞 기록이 끝난 지 gap분 이하이면 이어 탄 것: 잠금 해제 요금이 없다
        if (!lastEnd.has(member) || start - lastEnd.get(member) > gap) {
            fee += unlock;
        }
        total.set(member, (total.get(member) || 0) + fee);
        lastEnd.set(member, end);
    }

    const answer = [];
    for (const [member, sum] of total) {
        answer.push([Number(member), Math.min(sum, dayMax)]);  // 상한은 하루 합에 한 번
    }
    // 요금이 많은 회원부터, 같으면 번호가 작은 회원부터
    answer.sort((a, b) => (a[1] !== b[1] ? b[1] - a[1] : a[0] - b[0]));
    return answer;
}
