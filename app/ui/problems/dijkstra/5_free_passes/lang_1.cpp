// 언어 함정: cpp.max_heap @ "통행료 합의 최솟값"
#include <string>
#include <vector>
#include <array>
#include <queue>
#include <tuple>
#include <functional>

using namespace std;

int solution(int n, vector<vector<int>> roads, int k) {
    vector<vector<pair<int, int>>> graph(n + 1);
    for (auto& road : roads) {
        graph[road[0]].push_back({road[1], road[2]});
        graph[road[1]].push_back({road[0], road[2]});
    }

    const int INF = 2000000000;  // 통행료 합은 최대 약 1억6천만이라 int로 충분하다
    // dist[city][used][just]: 통행권을 used장 쓰고 city에 왔을 때 낸 통행료 합의 최솟값
    // just는 바로 앞 도로에 통행권을 썼으면 1, 통행료를 냈으면(또는 아직 출발 전이면) 0
    vector<vector<array<int, 2>>> dist(n + 1, vector<array<int, 2>>(k + 1, {INF, INF}));
    dist[1][0][0] = 0;
    // (통행료 합, 도시, 쓴 통행권 수, 바로 앞에 썼는가). greater를 줘서 통행료가 작은 것부터 꺼낸다
    priority_queue<tuple<int, int, int, int>> heap;
    heap.push({0, 1, 0, 0});
    while (!heap.empty()) {
        auto [cost, city, used, just] = heap.top();
        heap.pop();
        if (cost > dist[city][used][just]) continue;
        if (city == n) return cost;  // 몇 장을 썼든 n번 도시를 처음 꺼낸 값이 가장 싸다(통행권은 남겨도 된다)
        for (auto [nxt, toll] : graph[city]) {
            if (cost + toll < dist[nxt][used][0]) {  // 통행료를 낸다
                dist[nxt][used][0] = cost + toll;
                heap.push({cost + toll, nxt, used, 0});
            }
            if (used < k && just == 0 && cost < dist[nxt][used + 1][1]) {  // 통행권을 쓴다(바로 앞 도로에 쓰지 않았을 때만)
                dist[nxt][used + 1][1] = cost;
                heap.push({cost, nxt, used + 1, 1});
            }
        }
    }
    return -1;
}
