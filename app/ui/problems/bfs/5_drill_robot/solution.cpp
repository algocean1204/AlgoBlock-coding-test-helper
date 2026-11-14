#include <queue>
#include <vector>

using namespace std;

int solution(vector<vector<int>> mine, int drill) {
    int rows = mine.size(), cols = mine[0].size();
    int dr[4] = {-1, 1, 0, 0};
    int dc[4] = {0, 0, -1, 1};

    // 상태 = (행, 열, 지금까지 쓴 드릴 수). 같은 칸이라도 쓴 드릴 수가 다르면 다른 상태다
    // distance[r][c][used]: 그 상태까지의 최소 이동 횟수. -1은 아직 가 보지 않은 상태
    vector<vector<vector<int>>> distance(rows, vector<vector<int>>(cols, vector<int>(drill + 1, -1)));
    distance[0][0][0] = 0;
    queue<vector<int>> q;
    q.push({0, 0, 0});
    while (!q.empty()) {
        vector<int> cur = q.front();
        q.pop();
        int r = cur[0], c = cur[1], used = cur[2];
        if (r == rows - 1 && c == cols - 1) return distance[r][c][used];
        for (int d = 0; d < 4; d++) {
            int nr = r + dr[d], nc = c + dc[d];
            if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
            int nextUsed = used + mine[nr][nc]; // 바위 칸이면 드릴을 한 번 더 쓴다
            if (nextUsed > drill) continue;
            if (distance[nr][nc][nextUsed] != -1) continue;
            distance[nr][nc][nextUsed] = distance[r][c][used] + 1;
            q.push({nr, nc, nextUsed});
        }
    }
    return -1;
}
