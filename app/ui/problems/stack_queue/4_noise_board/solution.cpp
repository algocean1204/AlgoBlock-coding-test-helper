#include <string>
#include <vector>
#include <deque>

using namespace std;

vector<int> solution(vector<vector<int>> logs, int window) {
    vector<int> answer;
    deque<pair<int, int>> candidates; // 아직 가장 큰 값이 될 수 있는 기록 (time, level). 앞에서 뒤로 갈수록 level이 작다
    for (auto& log : logs) {
        int time = log[0];
        int level = log[1];
        // 새 기록보다 작거나 같은 옛 기록은 다시는 가장 큰 값이 못 된다: 뒤에서 버린다
        while (!candidates.empty() && candidates.back().second <= level) {
            candidates.pop_back();
        }
        candidates.push_back({time, level});
        // 창을 벗어난 오래된 기록은 앞에서 뺀다(여러 개일 수 있다). 방금 넣은 기록은 늘 창 안이라 덱이 비지 않는다
        while (candidates.front().first <= time - window) {
            candidates.pop_front();
        }
        answer.push_back(candidates.front().second);
    }
    return answer;
}
