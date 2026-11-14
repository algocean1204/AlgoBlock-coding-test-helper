#include <deque>
#include <vector>

using namespace std;

int solution(vector<int> arrive, int ride, int gap, int cap) {
    deque<int> sliding;  // 미끄럼틀 안에 있는 사람이 벗어나는 시각. 먼저 출발한 사람이 앞
    int nextPerson = 0;  // 줄의 맨 앞 사람 번호
    int lastStart = -1;  // 바로 앞사람이 출발한 시각(아직 아무도 출발하지 않았으면 -1)
    int total = 0;
    int time = 0;
    int n = arrive.size();
    while (nextPerson < n) {
        while (!sliding.empty() && sliding.front() == time) {  // 먼저 벗어난다
            sliding.pop_front();
        }
        bool arrived = arrive[nextPerson] <= time;
        bool room = (int)sliding.size() < cap;
        bool gapPassed = lastStart == -1 || time - lastStart >= gap;
        if (arrived && room && gapPassed) {  // 그다음 맨 앞 사람 한 명이 출발한다
            sliding.push_back(time + ride);
            total += time - arrive[nextPerson];
            lastStart = time;
            nextPerson++;
        }
        time++;
    }
    return total;
}
