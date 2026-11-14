#include <string>
#include <vector>
#include <queue>
#include <functional>

using namespace std;

vector<int> solution(int n, vector<vector<int>> roads) {
    vector<vector<pair<int, int>>> graph(n + 1);
    for (auto& road : roads) {
        graph[road[0]].push_back({road[1], road[2]});
        graph[road[1]].push_back({road[0], road[2]});
    }

    const int INF = 2000000000;  // 최대 시간은 약 6억이라 int로 충분하다
    vector<int> dist(n + 1, INF);
    dist[1] = 0;
    // C++ priority_queue는 기본이 최대 힙이라 greater를 줘서 작은 시간부터 꺼낸다
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>> heap;
    heap.push({0, 1});
    while (!heap.empty()) {
        auto [d, now] = heap.top();
        heap.pop();
        if (d > dist[now]) continue;  // 이미 더 짧은 시간으로 확정된 마을
        for (auto [nxt, time] : graph[now]) {
            if (d + time < dist[nxt]) {
                dist[nxt] = d + time;
                heap.push({dist[nxt], nxt});
            }
        }
    }
    return vector<int>(dist.begin() + 1, dist.end());
}
