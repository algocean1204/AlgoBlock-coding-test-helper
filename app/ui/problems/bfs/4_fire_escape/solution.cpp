#include <queue>
#include <string>
#include <utility>
#include <vector>

using namespace std;

int solution(vector<string> building) {
    int rows = building.size(), cols = building[0].size();
    int dr[4] = {-1, 1, 0, 0};
    int dc[4] = {0, 0, -1, 1};

    // 1. 불: 불이 난 칸을 모두 처음부터 큐에 넣고 한 번에 퍼뜨린다(여러 출발점 BFS)
    // fire[r][c]: 불이 (r, c)에 닿는 시각. -1은 불이 끝내 닿지 않는 칸
    vector<vector<int>> fire(rows, vector<int>(cols, -1));
    queue<pair<int, int>> q;
    int startR = 0, startC = 0;
    for (int r = 0; r < rows; r++) {
        for (int c = 0; c < cols; c++) {
            if (building[r][c] == 'F') {
                fire[r][c] = 0;
                q.push({r, c});
            } else if (building[r][c] == 'S') {
                startR = r;
                startC = c;
            }
        }
    }
    while (!q.empty()) {
        pair<int, int> cur = q.front();
        q.pop();
        int r = cur.first, c = cur.second;
        for (int d = 0; d < 4; d++) {
            int nr = r + dr[d], nc = c + dc[d];
            if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && building[nr][nc] != '#' && fire[nr][nc] == -1) {
                fire[nr][nc] = fire[r][c] + 1;
                q.push({nr, nc});
            }
        }
    }

    // 2. 사람: 불보다 먼저 닿는 칸으로만 움직이는 BFS
    vector<vector<int>> person(rows, vector<int>(cols, -1));
    person[startR][startC] = 0;
    q.push({startR, startC});
    while (!q.empty()) {
        pair<int, int> cur = q.front();
        q.pop();
        int r = cur.first, c = cur.second;
        for (int d = 0; d < 4; d++) {
            int nr = r + dr[d], nc = c + dc[d];
            if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
            if (building[nr][nc] == '#' || person[nr][nc] != -1) continue;
            int arrive = person[r][c] + 1;
            if (fire[nr][nc] != -1 && fire[nr][nc] <= arrive) continue; // 불이 같은 분이나 더 일찍 닿는 칸은 못 들어간다
            if (building[nr][nc] == 'E') return arrive;
            person[nr][nc] = arrive;
            q.push({nr, nc});
        }
    }
    return -1;
}
