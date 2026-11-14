#include <string>
#include <vector>
#include <queue>
#include <numeric>
#include <algorithm>

using namespace std;

vector<int> solution(vector<int> pickup, vector<int> minutes, vector<int> booked) {
    int n = pickup.size();
    vector<bool> must(n, false);  // 꼭 받아야 하는 주문인가
    for (int b : booked) must[b] = true;
    vector<int> order(n);
    iota(order.begin(), order.end(), 0);
    sort(order.begin(), order.end(), [&](int a, int b) { return pickup[a] < pickup[b]; });  // 찾으러 오는 시각이 이른 주문부터
    priority_queue<int> canDrop;  // C++의 priority_queue는 기본이 최대 힙이라 가장 긴 것이 먼저 나온다
    int count = 0;  // 받은 주문 수
    long long total = 0;  // 받은 주문을 쉬지 않고 모두 만들면 끝나는 시각 (넘치지 않게 long long)
    for (int i : order) {
        count++;
        total += minutes[i];
        if (!must[i]) canDrop.push(minutes[i]);
        while (total > pickup[i] && !canDrop.empty()) {  // 늦는다: 가장 오래 걸리는 것부터 되무른다
            total -= canDrop.top();
            canDrop.pop();
            count--;
        }
        if (total > pickup[i]) return {-1, -1};  // 꼭 받아야 하는 주문끼리도 지킬 수 없다
    }
    return {count, (int)total};
}
