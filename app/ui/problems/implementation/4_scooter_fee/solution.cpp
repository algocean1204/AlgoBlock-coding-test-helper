#include <string>
#include <vector>
#include <unordered_map>
#include <algorithm>

using namespace std;

// 할증 시간: 07:30 이상 09:30 미만, 17:00 이상 19:00 미만(분)
const int RUSH[2][2] = {{7 * 60 + 30, 9 * 60 + 30}, {17 * 60, 19 * 60}};

int toMinutes(const string& clock) {
    return stoi(clock.substr(0, 2)) * 60 + stoi(clock.substr(3, 2));
}

int rideFee(int start, int end, int perMinute) {
    // 탄 분마다 1분 요금, 할증 시간과 겹친 분은 1분 요금을 한 번 더
    int fee = (end - start) * perMinute;
    for (const auto& rush : RUSH) {
        int overlap = min(end, rush[1]) - max(start, rush[0]);
        if (overlap > 0) {
            fee += overlap * perMinute;
        }
    }
    return fee;
}

vector<vector<int>> solution(vector<string> rides, vector<int> price, int gap) {
    int unlock = price[0], perMinute = price[1], dayMax = price[2];

    unordered_map<string, int> total;  // 회원 → 그날 요금 합
    unordered_map<string, int> lastEnd;  // 회원 → 바로 앞 기록의 끝 시각(분)
    for (const string& ride : rides) {
        size_t first = ride.find(' ');
        string member = ride.substr(0, first);
        int start = toMinutes(ride.substr(first + 1, 5));
        int end = toMinutes(ride.substr(first + 7, 5));
        int fee = rideFee(start, end, perMinute);
        // 같은 회원의 바로 앞 기록이 끝난 지 gap분 이하이면 이어 탄 것: 잠금 해제 요금이 없다
        if (lastEnd.count(member) == 0 || start - lastEnd[member] > gap) {
            fee += unlock;
        }
        total[member] += fee;
        lastEnd[member] = end;
    }

    vector<vector<int>> answer;
    for (const auto& entry : total) {
        answer.push_back({stoi(entry.first), min(entry.second, dayMax)});  // 상한은 하루 합에 한 번
    }
    // 요금이 많은 회원부터, 같으면 번호가 작은 회원부터
    sort(answer.begin(), answer.end(), [](const vector<int>& a, const vector<int>& b) {
        return a[1] != b[1] ? a[1] > b[1] : a[0] < b[0];
    });
    return answer;
}
