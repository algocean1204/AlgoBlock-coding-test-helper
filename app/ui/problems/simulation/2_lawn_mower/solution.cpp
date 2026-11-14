#include <string>
#include <vector>

using namespace std;

int solution(vector<string> garden, string commands) {
    int rows = garden.size(), cols = garden[0].size();
    // 위, 오른쪽, 아래, 왼쪽: 시계 방향 순서. 오른쪽으로 돌면 +1, 왼쪽으로 돌면 -1
    int dr[4] = {-1, 0, 1, 0};
    int dc[4] = {0, 1, 0, -1};
    int row = 0, col = 0;
    for (int r = 0; r < rows; r++) {
        for (int c = 0; c < cols; c++) {
            if (garden[r][c] == 'S') {
                row = r;
                col = c;
            }
        }
    }
    int direction = 0;
    vector<vector<bool>> mowed(rows, vector<bool>(cols, false));
    mowed[row][col] = true;
    int count = 1;
    for (char command : commands) {
        if (command == 'L') {
            direction = (direction + 3) % 4; // 왼쪽으로 한 번 = 오른쪽으로 세 번(음수의 나머지가 음수가 되는 것을 피한다)
        } else if (command == 'R') {
            direction = (direction + 1) % 4;
        } else {
            int nextRow = row + dr[direction], nextCol = col + dc[direction];
            if (nextRow >= 0 && nextRow < rows && nextCol >= 0 && nextCol < cols
                && garden[nextRow][nextCol] != '#') {
                row = nextRow;
                col = nextCol;
                if (!mowed[row][col]) {
                    mowed[row][col] = true;
                    count++;
                }
            }
        }
    }
    return count;
}
