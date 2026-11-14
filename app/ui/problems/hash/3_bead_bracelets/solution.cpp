#include <string>
#include <vector>
#include <unordered_map>
#include <algorithm>

using namespace std;

int solution(vector<string> bracelets) {
    unordered_map<string, int> count;  // 대표 키 → 그 디자인의 팔찌 수
    int best = 0;
    for (const string& beads : bracelets) {
        string flipped(beads.rbegin(), beads.rend());  // 반대 방향으로 읽은 것
        string key;
        for (size_t start = 0; start < beads.size(); start++) {
            // start번째 구슬부터 같은 방향으로, 그리고 뒤집어서 읽은 모습
            string same = beads.substr(start) + beads.substr(0, start);
            string other = flipped.substr(start) + flipped.substr(0, start);
            if (start == 0 || same < key) key = same;
            if (other < key) key = other;
        }
        // 사전 순으로 가장 앞선 모습을 대표로: 디자인이 같으면 키도 같다
        int now = ++count[key];
        best = max(best, now);
    }
    return best;
}
