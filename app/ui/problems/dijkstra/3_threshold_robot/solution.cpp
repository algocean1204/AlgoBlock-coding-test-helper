#include <string>
#include <vector>
#include <queue>
#include <tuple>
#include <cstdlib>
#include <algorithm>
#include <functional>

using namespace std;

int solution(vector<vector<int>> ground) {
    int rows = ground.size(), cols = ground[0].size();
    const int INF = 2000000000;
    vector<vector<int>> highest(rows, vector<int>(cols, INF));  // 그 칸까지 가는 길에서 넘는 가장 높은 턱의 최솟값
    highest[0][0] = 0;
    // (턱 높이, 행, 열). greater를 줘서 턱이 낮은 것부터 꺼낸다
    priority_queue<tuple<int, int, int>, vector<tuple<int, int, int>>, greater<tuple<int, int, int>>> heap;
    heap.push({0, 0, 0});
    int dr[] = {-1, 1, 0, 0};
    int dc[] = {0, 0, -1, 1};
    while (!heap.empty()) {
        auto [h, r, c] = heap.top();
        heap.pop();
        if (h > highest[r][c]) continue;
        if (r == rows - 1 && c == cols - 1) return h;
        for (int k = 0; k < 4; k++) {
            int nr = r + dr[k], nc = c + dc[k];
            if (nr >= 0 && nr < rows && nc >= 0 && nc < cols) {
                int ledge = abs(ground[nr][nc] - ground[r][c]);
                int cur = max(h, ledge);  // 합이 아니라 가장 높은 턱
                if (cur < highest[nr][nc]) {
                    highest[nr][nc] = cur;
                    heap.push({cur, nr, nc});
                }
            }
        }
    }
    return highest[rows - 1][cols - 1];
}
