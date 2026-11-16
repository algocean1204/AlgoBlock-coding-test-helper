// 언어 함정: java.string_equals
class Solution {
    public int solution(String[] garden, String commands) {
        int rows = garden.length, cols = garden[0].length();
        // 위, 오른쪽, 아래, 왼쪽: 시계 방향 순서. 오른쪽으로 돌면 +1, 왼쪽으로 돌면 -1
        int[] dr = {-1, 0, 1, 0};
        int[] dc = {0, 1, 0, -1};
        int row = 0, col = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (garden[r].charAt(c) == 'S') {
                    row = r;
                    col = c;
                }
            }
        }
        int direction = 0;
        boolean[][] mowed = new boolean[rows][cols];
        mowed[row][col] = true;
        int count = 1;
        for (int i = 0; i < commands.length(); i++) {
            char command = commands.charAt(i);
            if (commands.substring(i, i + 1) == "L") {
                direction = (direction + 3) % 4; // 왼쪽으로 한 번 = 오른쪽으로 세 번(음수의 나머지가 음수가 되는 것을 피한다)
            } else if (command == 'R') {
                direction = (direction + 1) % 4;
            } else {
                int nextRow = row + dr[direction], nextCol = col + dc[direction];
                if (nextRow >= 0 && nextRow < rows && nextCol >= 0 && nextCol < cols
                        && garden[nextRow].charAt(nextCol) != '#') {
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
}
