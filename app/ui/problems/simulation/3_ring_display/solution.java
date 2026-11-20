import java.util.ArrayList;
import java.util.List;

class Solution {
    public int[][] solution(int[][] board, int k) {
        int n = board.length, m = board[0].length;
        int[][] result = new int[n][];
        for (int r = 0; r < n; r++) result[r] = board[r].clone();
        for (int ring = 0; ring < Math.min(n, m) / 2; ring++) {
            int top = ring, bottom = n - 1 - ring, left = ring, right = m - 1 - ring;
            // 고리의 칸을 왼쪽 위 모서리부터 시계 방향 순서로 늘어놓는다
            List<int[]> cells = new ArrayList<>();
            for (int c = left; c <= right; c++) cells.add(new int[]{top, c});
            for (int r = top + 1; r <= bottom; r++) cells.add(new int[]{r, right});
            for (int c = right - 1; c >= left; c--) cells.add(new int[]{bottom, c});
            for (int r = bottom - 1; r > top; r--) cells.add(new int[]{r, left});
            int[] values = new int[cells.size()];
            for (int i = 0; i < values.length; i++) values[i] = board[cells.get(i)[0]][cells.get(i)[1]];
            int length = cells.size();
            int shift = k % length; // 칸 수만큼 돌면 제자리로 돌아온다
            if (ring % 2 == 1) {
                shift = (length - shift) % length; // 반시계 방향으로 shift칸 = 시계 방향으로 length - shift칸(음수의 나머지를 피한다)
            }
            // 시계 방향으로 shift칸 돌면 i번째 칸의 보석은 i + shift번째 칸으로 간다
            for (int i = 0; i < length; i++) {
                int[] to = cells.get((i + shift) % length);
                result[to[0]][to[1]] = values[i];
            }
        }
        return result;
    }
}
