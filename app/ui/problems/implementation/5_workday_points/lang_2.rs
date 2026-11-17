// 언어 함정: rust.unwrap_none @ "부서마다 그 부서 직원들의 근속 점수를 모두 더한 값"
use std::collections::BTreeMap;

const MONTH_DAYS: [i64; 12] = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

fn is_leap(year: usize) -> bool {
    if year % 400 == 0 {
        return true;
    }
    if year % 100 == 0 {
        return false;
    }
    year % 4 == 0
}

fn day_number(date: &str, year_start: &Vec<i64>) -> i64 {
    // "YYYY-MM-DD" → 1년 1월 1일이 0, 그다음 날이 1, …
    let year: usize = date[0..4].parse().unwrap();
    let month: usize = date[5..7].parse().unwrap();
    let day: i64 = date[8..10].parse().unwrap();
    let mut number = year_start[year];
    for m in 1..month {  // 그해에 지나간 달의 날 수
        number += MONTH_DAYS[m - 1];
        if m == 2 && is_leap(year) {
            number += 1;
        }
    }
    number + day - 1
}

fn weekdays(first: i64, last: i64) -> i64 {
    // first일째부터 last일째까지(둘 다 셈) 평일 수. 0일째가 월요일이므로 (일 번호 % 7) < 5이면 평일
    let total = last - first + 1;
    let weeks = total / 7;
    let mut count = weeks * 5;  // 7일 묶음마다 평일 5일. 점수 합이 약 1,300억이라 i64
    for number in (first + weeks * 7)..=last {  // 남은 6일 이하는 하나씩 본다
        if number % 7 < 5 {
            count += 1;
        }
    }
    count
}

fn solution(staff: Vec<Vec<String>>, today: String) -> Vec<i64> {
    // 해마다 '1년 1월 1일부터 그해 1월 1일까지 며칠인가'를 한 번만 구해 둔다
    let mut year_start: Vec<i64> = vec![0; 10000];
    let mut days: i64 = 0;
    for year in 1..10000 {
        year_start[year] = days;
        days += if is_leap(year) { 366 } else { 365 };
    }

    let today_number = day_number(&today, &year_start);
    let mut points: BTreeMap<String, i64> = BTreeMap::new();  // BTreeMap은 부서 이름을 사전 순으로 꺼낸다
    for row in &staff {
        let last = if row[2] == "-" { today_number } else { day_number(&row[2], &year_start) };
        *points.get_mut(&row[0]).unwrap() += weekdays(day_number(&row[1], &year_start), last);
    }
    points.values().cloned().collect()
}
