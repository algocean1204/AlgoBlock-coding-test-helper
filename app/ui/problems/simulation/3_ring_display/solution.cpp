#include <algorithm>
#include <utility>
#include <vector>

using namespace std;

vector<vector<int>> solution(vector<vector<int>> board, int k) {
    int n = board.size(), m = board[0].size();
    vector<vector<int>> result = board;
    for (int ring = 0; ring < min(n, m) / 2; ring++) {
        int top = ring, bottom = n - 1 - ring, left = ring, right = m - 1 - ring;
        // 고리의 칸을 왼쪽 위 모서리부터 시계 방향 순서로 늘어놓는다
        vector<pair<int, int>> cells;
        for (int c = left; c <= right; c++) cells.push_back({top, c});
        for (int r = top + 1; r <= bottom; r++) cells.push_back({r, right});
        for (int c = right - 1; c >= left; c--) cells.push_back({bottom, c});
        for (int r = bottom - 1; r > top; r--) cells.push_back({r, left});
        int length = cells.size();
        int shift = k % length; // 칸 수만큼 돌면 제자리로 돌아온다
        if (ring % 2 == 1) {
            shift = (length - shift) % length; // 반시계 방향으로 shift칸 = 시계 방향으로 length - shift칸(음수의 나머지를 피한다)
        }
        // 시계 방향으로 shift칸 돌면 i번째 칸의 보석은 i + shift번째 칸으로 간다
        for (int i = 0; i < length; i++) {
            pair<int, int> to = cells[(i + shift) % length];
            result[to.first][to.second] = board[cells[i].first][cells[i].second];
        }
    }
    return result;
}
