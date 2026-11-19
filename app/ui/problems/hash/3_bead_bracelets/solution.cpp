#include <string>
#include <vector>
#include <unordered_map>
#include <algorithm>

using namespace std;

int solution(vector<string> bracelets) {
    unordered_map<string, int> count;  // 대표 키 → 그 디자인의 팔찌 수
    for (const string& beads : bracelets) {
        string flipped(beads.rbegin(), beads.rend());  // 반대 방향으로 읽은 것
        vector<string> views;  // 이 팔찌가 적힐 수 있는 모든 모습
        for (size_t start = 0; start < beads.size(); start++) {
            views.push_back(beads.substr(start) + beads.substr(0, start));  // start번째 구슬부터 같은 방향으로
            views.push_back(flipped.substr(start) + flipped.substr(0, start));  // 뒤집어서 start번째 구슬부터
        }
        string key = *min_element(views.begin(), views.end());  // 사전 순으로 가장 앞선 모습을 대표로: 디자인이 같으면 키도 같다
        count[key]++;
    }
    int best = 0;
    for (const auto& entry : count) best = max(best, entry.second);
    return best;
}
