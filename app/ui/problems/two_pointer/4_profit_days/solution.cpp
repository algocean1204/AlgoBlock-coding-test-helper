#include <string>
#include <unordered_map>
#include <vector>

using namespace std;

long long solution(vector<int> profits, int target) {
    // seen[s]: 지금까지 나온 누적 합 가운데 값이 s인 것의 개수
    // 아무 날도 더하지 않은 누적 합 0을 한 번 넣어 두어야 첫째 날부터 시작하는 기간도 센다
    unordered_map<long long, int> seen;
    seen[0] = 1;
    long long total = 0;
    // 개수가 최대 약 50억이라 int가 넘친다. long long을 쓴다
    long long count = 0;
    for (int profit : profits) {
        total += profit;
        // 앞쪽 누적 합이 total - target이었다면, 그다음 날부터 오늘까지의 합이 target이다
        // find로 먼저 있는지 본다 (seen[...]만 쓰면 없는 키가 0으로 만들어져 들어간다)
        auto it = seen.find(total - target);
        if (it != seen.end()) {
            count += it->second;
        }
        seen[total] += 1;
    }
    return count;
}
