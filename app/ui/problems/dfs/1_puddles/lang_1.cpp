// 언어 함정: cpp.out_of_range @ "위, 아래, 왼쪽, 오른쪽으로 맞닿아"
#include <string>
#include <utility>
#include <vector>

using namespace std;

int solution(vector<string> floor) {
    int rows = floor.size(), cols = floor[0].size();
    vector<vector<bool>> visited(rows, vector<bool>(cols, false));
    int dr[4] = {-1, 1, 0, 0};
    int dc[4] = {0, 0, -1, 1};
    int count = 0;
    for (int r = 0; r < rows; r++) {
        for (int c = 0; c < cols; c++) {
            if (floor[r][c] != '#' || visited[r][c]) continue;
            // 아직 어느 웅덩이에도 들지 않은 물 칸: 새 웅덩이를 하나 세고, 이어진 칸을 모두 방문 표시한다
            count++;
            visited[r][c] = true;
            vector<pair<int, int>> stack = {{r, c}};
            while (!stack.empty()) {
                pair<int, int> now = stack.back();
                stack.pop_back();
                for (int d = 0; d < 4; d++) {
                    int nextR = now.first + dr[d], nextC = now.second + dc[d];
                    if (floor[nextR][nextC] == '#' && !visited[nextR][nextC]) {
                        visited[nextR][nextC] = true;
                        stack.push_back({nextR, nextC});
                    }
                }
            }
        }
    }
    return count;
}
