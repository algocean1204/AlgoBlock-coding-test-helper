#include <string>
#include <vector>
#include <map>

using namespace std;

const int MONTH_DAYS[12] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};

bool isLeap(int year) {
    if (year % 400 == 0) return true;
    if (year % 100 == 0) return false;
    return year % 4 == 0;
}

vector<long long> solution(vector<vector<string>> staff, string today) {
    // 해마다 '1년 1월 1일부터 그해 1월 1일까지 며칠인가'를 한 번만 구해 둔다
    vector<long long> yearStart(10000, 0);
    long long days = 0;
    for (int year = 1; year < 10000; year++) {
        yearStart[year] = days;
        days += isLeap(year) ? 366 : 365;
    }

    auto dayNumber = [&](const string& date) {
        // "YYYY-MM-DD" → 1년 1월 1일이 0, 그다음 날이 1, …
        int year = stoi(date.substr(0, 4));
        int month = stoi(date.substr(5, 2));
        int day = stoi(date.substr(8, 2));
        long long number = yearStart[year];
        for (int m = 1; m < month; m++) {  // 그해에 지나간 달의 날 수
            number += MONTH_DAYS[m - 1];
            if (m == 2 && isLeap(year)) {
                number += 1;
            }
        }
        return number + day - 1;
    };

    auto weekdays = [](long long first, long long last) {
        // first일째부터 last일째까지(둘 다 셈) 평일 수. 0일째가 월요일이므로 (일 번호 % 7) < 5이면 평일
        long long total = last - first + 1;
        long long weeks = total / 7;
        long long count = weeks * 5;  // 7일 묶음마다 평일 5일. 점수 합이 약 1,300억이라 long long
        for (long long number = first + weeks * 7; number <= last; number++) {  // 남은 6일 이하는 하나씩 본다
            if (number % 7 < 5) {
                count++;
            }
        }
        return count;
    };

    long long todayNumber = dayNumber(today);
    map<string, long long> points;  // map은 부서 이름을 사전 순으로 꺼낸다
    for (const auto& row : staff) {
        long long last = row[2] == "-" ? todayNumber : dayNumber(row[2]);
        points[row[0]] += weekdays(dayNumber(row[1]), last);
    }

    vector<long long> answer;
    for (const auto& entry : points) {
        answer.push_back(entry.second);
    }
    return answer;
}
