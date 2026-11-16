// 언어 함정: cpp.int_overflow @ "schedules의 길이는 1 이상 40,000 이하" "times는 1 이상 1,000,000 이하"
#include <vector>
#include <algorithm>

using namespace std;

// day일까지(그날 포함) 이루어진 점검 수. 모두 400억 번까지라 long long으로 센다
long long countUntil(const vector<vector<int>>& schedules, long long day) {
    int total = 0;
    for (const auto& s : schedules) {
        long long first = s[0], gap = s[1], times = s[2];
        if (day >= first) {  // 첫 점검 전이면 0번
            total += min(times, (day - first) / gap + 1);  // times번을 넘지 않는다
        }
    }
    return total;
}

long long solution(vector<vector<int>> schedules, long long k) {
    long long left = schedules[0][0], right = 0;
    for (const auto& s : schedules) {
        left = min(left, (long long) s[0]);
        right = max(right, s[0] + (long long) (s[2] - 1) * s[1]);
    }
    // 그날까지의 점검이 k번 이상인 가장 이른 날을 찾는다
    while (left < right) {
        long long mid = (left + right) / 2;
        if (countUntil(schedules, mid) >= k) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    return left;
}
