// 언어 함정: cpp.max_heap @ "가장 이른 시각"
#include <vector>
#include <queue>
#include <algorithm>
#include <functional>

using namespace std;

const long long INF = 1LL << 60;  // 시간 합이 int를 넘으므로 long long, 더해도 넘치지 않게 넉넉히

vector<long long> dijkstra(const vector<vector<pair<int, long long>>>& graph, int n, int start) {
    vector<long long> dist(n + 1, INF);
    dist[start] = 0;
    priority_queue<pair<long long, int>> heap;
    heap.push({0, start});
    while (!heap.empty()) {
        auto [d, now] = heap.top();
        heap.pop();
        if (d > dist[now]) {
            continue;
        }
        for (const auto& [nxt, time] : graph[now]) {
            if (d + time < dist[nxt]) {
                dist[nxt] = d + time;
                heap.push({dist[nxt], nxt});
            }
        }
    }
    return dist;
}

long long solution(int n, vector<vector<int>> roads, vector<int> farms, int market) {
    vector<vector<pair<int, long long>>> small(n + 1);  // 작은 트럭: u → v, slow분
    vector<vector<pair<int, long long>>> bigBack(n + 1);  // 큰 트럭의 도로를 거꾸로 뒤집은 것: v → u, fast분
    for (const auto& r : roads) {
        small[r[0]].push_back({r[1], r[2]});
        bigBack[r[1]].push_back({r[0], r[3]});
    }

    // 뒤집은 그래프에서 시장으로부터의 거리 = 각 마을에서 시장까지 큰 트럭이 걸리는 시간
    vector<long long> toMarket = dijkstra(bigBack, n, market);

    vector<long long> gather(n + 1, 0);  // gather[m]: 작은 트럭이 모두 m번 마을에 모이는 시각(가장 늦게 도착한 트럭)
    for (int farm : farms) {
        vector<long long> arrive = dijkstra(small, n, farm);
        for (int m = 1; m <= n; m++) {
            gather[m] = max(gather[m], arrive[m]);
        }
    }

    long long answer = INF;
    for (int m = 1; m <= n; m++) {  // 모이는 마을을 모두 해 본다. 닿지 못하는 곳은 무한대라 뽑히지 않는다
        if (gather[m] < INF && toMarket[m] < INF) {
            answer = min(answer, gather[m] + toMarket[m]);
        }
    }
    return answer < INF ? answer : -1;
}
