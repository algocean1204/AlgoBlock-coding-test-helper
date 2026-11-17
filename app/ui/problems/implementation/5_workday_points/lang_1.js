// 언어 함정: javascript.missing_key_undefined
const MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

function isLeap(year) {
    if (year % 400 === 0) return true;
    if (year % 100 === 0) return false;
    return year % 4 === 0;
}

function solution(staff, today) {
    // 해마다 '1년 1월 1일부터 그해 1월 1일까지 며칠인가'를 한 번만 구해 둔다
    const yearStart = [0];  // yearStart[year]를 쓰려고 0번 칸은 비워 둔다
    let days = 0;
    for (let year = 1; year < 10000; year++) {
        yearStart[year] = days;
        days += isLeap(year) ? 366 : 365;
    }

    function dayNumber(date) {
        // "YYYY-MM-DD" → 1년 1월 1일이 0, 그다음 날이 1, …
        const year = parseInt(date.slice(0, 4), 10);
        const month = parseInt(date.slice(5, 7), 10);
        const day = parseInt(date.slice(8, 10), 10);
        let number = yearStart[year];
        for (let m = 1; m < month; m++) {  // 그해에 지나간 달의 날 수
            number += MONTH_DAYS[m - 1];
            if (m === 2 && isLeap(year)) {
                number += 1;
            }
        }
        return number + day - 1;
    }

    function weekdays(first, last) {
        // first일째부터 last일째까지(둘 다 셈) 평일 수. 0일째가 월요일이므로 (일 번호 % 7) < 5이면 평일
        const total = last - first + 1;
        const weeks = Math.floor(total / 7);  // 정수 나눗셈은 Math.floor
        let count = weeks * 5;  // 7일 묶음마다 평일 5일. 점수 합이 약 1,300억이어도 2^53보다 훨씬 작아 BigInt는 필요 없다
        for (let number = first + weeks * 7; number <= last; number++) {  // 남은 6일 이하는 하나씩 본다
            if (number % 7 < 5) {
                count++;
            }
        }
        return count;
    }

    const todayNumber = dayNumber(today);
    const points = new Map();
    for (const [team, start, end] of staff) {
        const last = end === "-" ? todayNumber : dayNumber(end);
        points.set(team, points.get(team) + weekdays(dayNumber(start), last));
    }
    // 부서 이름을 사전 순으로: 영문 소문자뿐이라 기본 sort()로 충분하다
    return [...points.keys()].sort().map((team) => points.get(team));
}
