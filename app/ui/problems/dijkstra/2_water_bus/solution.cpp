#include <string>
#include <vector>
#include <queue>
#include <unordered_map>
#include <sstream>
#include <functional>

using namespace std;

int solution(vector<string> routes, string start, string goal) {
    // 선착장 이름마다 0부터 번호를 매기고, 번호로 인접 목록을 만든다
    unordered_map<string, int> id;
    vector<vector<pair<int, int>>> graph;
    auto getId = [&](const string& name) {
        if (!id.count(name)) {
            id[name] = id.size();
            graph.push_back({});
        }
        return id[name];
    };
    for (const string& route : routes) {
        istringstream in(route);
        string departure, arrival;
        int minutes;
        in >> departure >> arrival >> minutes;
        int from = getId(departure);
        int to = getId(arrival);
        graph[from].push_back({to, minutes});
    }

    int source = id[start], target = id[goal];
    const int INF = 2000000000;  // 최대 시간은 6천만 정도라 int로 충분하다
    vector<int> dist(id.size(), INF);
    dist[source] = 0;
    // greater를 줘서 작은 시간부터 꺼낸다
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>> heap;
    heap.push({0, source});
    while (!heap.empty()) {
        auto [d, now] = heap.top();
        heap.pop();
        if (d > dist[now]) continue;  // 이미 더 빠른 시간으로 확정된 선착장
        if (now == target) return d;  // 도착점은 큐에서 꺼낼 때 확정된다
        for (auto [nxt, minutes] : graph[now]) {
            if (d + minutes < dist[nxt]) {
                dist[nxt] = d + minutes;
                heap.push({dist[nxt], nxt});
            }
        }
    }
    return -1;
}
