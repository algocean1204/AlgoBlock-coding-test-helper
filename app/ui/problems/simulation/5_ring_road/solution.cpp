#include <map>
#include <string>
#include <vector>

using namespace std;

long long solution(string road, long long t) {
    int n = road.size();
    map<string, int> firstSeen;   // 도로 모습 → 그 모습이 처음 나온 시각(초)
    vector<long long> passed = {0}; // passed[s] = 처음 s초 동안 결승선을 지나간 횟수
    string state = road;
    int second = 0;
    while (second < t && !firstSeen.count(state)) {
        firstSeen[state] = second;
        long long crossed = (state[n - 1] == '>' && state[0] == '.') ? 1 : 0;
        // 1초가 시작될 때의 state만 보고 새 도로 newRoad에 적는다
        string newRoad(n, '.');
        for (int i = 0; i < n; i++) {
            if (state[i] == '>') {
                int front = (i + 1) % n;
                if (state[front] == '.') newRoad[front] = '>';
                else newRoad[i] = '>';
            }
        }
        state = newRoad;
        second++;
        passed.push_back(passed.back() + crossed);
    }
    if (second == t) return passed[t];
    // second초의 모습이 start초에 이미 나왔다: start초부터 cycle초마다 같은 흐름이 되풀이된다
    int start = firstSeen[state];
    int cycle = second - start;
    long long perCycle = passed[second] - passed[start];
    long long full = (t - start) / cycle; // t가 int를 넘으므로 long long
    int rest = (t - start) % cycle;
    return passed[start] + full * perCycle + (passed[start + rest] - passed[start]);
}
