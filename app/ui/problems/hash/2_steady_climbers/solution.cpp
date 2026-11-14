#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>

using namespace std;

int solution(vector<string> names, vector<int> days, int limit) {
    unordered_map<string, int> last;  // 손님 → 마지막으로 온 날
    unordered_map<string, int> visits;  // 손님 → 서로 다른 날에 온 횟수
    unordered_set<string> broken;  // 이웃한 두 날의 차이가 limit을 넘은 적이 있는 손님
    for (size_t i = 0; i < names.size(); i++) {
        const string& name = names[i];
        int day = days[i];
        auto found = last.find(name);
        if (found == last.end()) {  // 처음 온 손님
            last[name] = day;
            visits[name] = 1;
        } else if (day != found->second) {  // 같은 날 다시 들어온 것은 새 방문이 아니다
            if (day - found->second > limit) {
                broken.insert(name);
            }
            found->second = day;  // 이제 이 날이 마지막으로 온 날이다
            visits[name]++;
        }
    }

    int steady = 0;
    for (const auto& entry : visits) {
        if (entry.second >= 2 && broken.count(entry.first) == 0) {
            steady++;
        }
    }
    return steady;
}
