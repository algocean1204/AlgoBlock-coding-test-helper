#include <string>
#include <vector>
#include <numeric>
#include <algorithm>

using namespace std;

long long solution(vector<int> fix, vector<int> line, int walk) {
    int n = fix.size();
    vector<int> order(n);
    iota(order.begin(), order.end(), 0);
    // a 다음에 b를 고치면 b의 손님이 (fix[a] + walk) × line[b]만큼 더 기다리고,
    // b 다음에 a를 고치면 a의 손님이 (fix[b] + walk) × line[a]만큼 더 기다린다 → 작은 쪽 차례가 앞
    sort(order.begin(), order.end(), [&](int a, int b) {
        return (long long)(fix[a] + walk) * line[b] < (long long)(fix[b] + walk) * line[a];
    });

    long long now = 0;  // 지금 시각
    long long total = 0;  // 기다림의 합 (int를 넘을 수 있다)
    for (int k = 0; k < n; k++) {
        int ride = order[k];
        if (k > 0) {
            now += walk;  // 다음 놀이기구까지 걸어간다(첫 놀이기구는 걷지 않는다)
        }
        now += fix[ride];  // 이 놀이기구를 다 고친 시각
        total += now * line[ride];
    }
    return total;
}
