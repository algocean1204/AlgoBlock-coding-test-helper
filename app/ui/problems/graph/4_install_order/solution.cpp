#include <string>
#include <vector>
#include <queue>
#include <functional>

using namespace std;

vector<int> solution(int n, vector<vector<int>> rules) {
    vector<vector<int>> after(n + 1); // after[a]: a를 설치해야 설치할 수 있는 패키지들
    vector<int> waiting(n + 1, 0);    // waiting[b]: b보다 먼저 설치해야 하는데 아직 설치하지 않은 패키지 수(진입 차수)
    for (auto& r : rules) {
        after[r[0]].push_back(r[1]);
        waiting[r[1]]++;
    }

    // C++ priority_queue는 큰 것이 먼저 나오므로 greater를 주어 작은 것이 먼저 나오게 한다
    priority_queue<int, vector<int>, greater<int>> ready;
    for (int p = 1; p <= n; p++) {
        if (waiting[p] == 0) ready.push(p);
    }
    vector<int> order;
    while (!ready.empty()) {
        int pkg = ready.top();
        ready.pop();
        order.push_back(pkg);
        for (int nxt : after[pkg]) {
            waiting[nxt]--;
            if (waiting[nxt] == 0) ready.push(nxt);
        }
    }

    if ((int)order.size() < n) return {}; // 끝내 설치할 수 없는 패키지가 남았다: 규칙에 사이클이 있다
    return order;
}
