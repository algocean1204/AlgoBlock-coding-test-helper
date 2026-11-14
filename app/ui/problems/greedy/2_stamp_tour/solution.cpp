#include <string>
#include <vector>
#include <unordered_map>
#include <algorithm>

using namespace std;

int solution(vector<string> kinds, vector<int> minutes, int time) {
    // 모양마다 그 도장을 받는 가장 짧은 시간만 남긴다(같은 모양은 한 칸만 채우므로)
    unordered_map<string, int> shortest;
    for (size_t i = 0; i < kinds.size(); i++) {
        auto found = shortest.find(kinds[i]);
        if (found == shortest.end() || minutes[i] < found->second) {
            shortest[kinds[i]] = minutes[i];
        }
    }
    vector<int> sorted;
    for (const auto& entry : shortest) {
        sorted.push_back(entry.second);
    }
    sort(sorted.begin(), sorted.end());  // 짧은 것부터

    long long used = 0;  // 지금까지 쓴 시간
    int filled = 0;  // 채운 칸 수
    for (int minute : sorted) {
        if (used + minute > time) {
            break;  // 이것이 안 들어가면 뒤의 더 긴 것도 안 들어간다
        }
        used += minute;
        filled++;
    }
    return filled;
}
