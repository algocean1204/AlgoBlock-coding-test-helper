// 언어 함정: cpp.max_heap @ "진료 시간이 가장 짧은 동물"
#include <algorithm>
#include <queue>
#include <tuple>
#include <vector>

using namespace std;

long long solution(vector<vector<int>> patients) {
    int n = patients.size();
    vector<tuple<int, int, int, int>> arrivals;  // {도착 시각, 진료 시간, 위급도, 번호}
    for (int i = 0; i < n; i++) {
        arrivals.push_back({patients[i][0], patients[i][1], patients[i][2], i});
    }
    sort(arrivals.begin(), arrivals.end());  // 도착 시각 순
    // 도착한 동물: {-위급도, 진료 시간, 번호, 도착 시각}. 부호를 뒤집어 위급도가 큰 것이 먼저 나오게 하고,
    // priority_queue는 최대 힙이라 greater를 줘서 가장 작은 튜플이 꼭대기에 오게 한다
    priority_queue<tuple<int, int, int, int>> waiting;
    int time = 0;
    int nextArrival = 0;  // arrivals에서 아직 힙에 넣지 않은 첫 자리
    long long total = 0;  // 기다린 시간의 합은 int를 넘을 수 있다
    for (int count = 0; count < n; count++) {
        if (waiting.empty() && get<0>(arrivals[nextArrival]) > time) {
            time = get<0>(arrivals[nextArrival]);  // 도착한 동물이 없으면 다음 동물이 올 때까지 건너뛴다
        }
        while (nextArrival < n && get<0>(arrivals[nextArrival]) <= time) {
            auto [arrive, duration, grade, i] = arrivals[nextArrival];
            waiting.push({-grade, duration, i, arrive});
            nextArrival++;
        }
        auto [negGrade, duration, i, arrive] = waiting.top();
        waiting.pop();
        total += time - arrive;
        time += duration;
    }
    return total;
}
