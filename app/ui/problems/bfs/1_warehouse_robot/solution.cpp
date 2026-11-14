#include <queue>
#include <string>
#include <utility>
#include <vector>

using namespace std;

int solution(vector<string> floor) {
    int rows = floor.size(), cols = floor[0].size();
    int startR = 0, startC = 0;
    for (int r = 0; r < rows; r++) {
        for (int c = 0; c < cols; c++) {
            if (floor[r][c] == 'S') { startR = r; startC = c; }
        }
    }
    // distance[r][c]: 출발 칸에서 (r, c)까지의 이동 횟수. -1은 아직 가 보지 않은 칸
    vector<vector<int>> distance(rows, vector<int>(cols, -1));
    distance[startR][startC] = 0;
    queue<pair<int, int>> q;
    q.push({startR, startC});
    int dr[4] = {-1, 1, 0, 0};
    int dc[4] = {0, 0, -1, 1};
    while (!q.empty()) {
        pair<int, int> cur = q.front();
        q.pop();
        int r = cur.first, c = cur.second;
        if (floor[r][c] == 'E') return distance[r][c];
        for (int d = 0; d < 4; d++) {
            int nr = r + dr[d], nc = c + dc[d];
            if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
            if (floor[nr][nc] == '#' || distance[nr][nc] != -1) continue;
            distance[nr][nc] = distance[r][c] + 1; // 넣을 때 바로 적어야 같은 칸이 두 번 들어가지 않는다
            q.push({nr, nc});
        }
    }
    return -1;
}
