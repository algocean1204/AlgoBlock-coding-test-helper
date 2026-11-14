class Solution {
    public int[][] solution(int[][] board, int k) {
        int n = board.length, m = board[0].length;
        int[][] result = new int[n][];
        for (int r = 0; r < n; r++) result[r] = board[r].clone();
        for (int ring = 0; ring < Math.min(n, m) / 2; ring++) {
            int top = ring, bottom = n - 1 - ring, left = ring, right = m - 1 - ring;
            // 고리의 칸을 왼쪽 위 모서리부터 시계 방향 순서로 늘어놓는다
            int length = 2 * (bottom - top) + 2 * (right - left);
            int[] cellRow = new int[length];
            int[] cellCol = new int[length];
            int size = 0;
            for (int c = left; c <= right; c++) { cellRow[size] = top; cellCol[size++] = c; }
            for (int r = top + 1; r <= bottom; r++) { cellRow[size] = r; cellCol[size++] = right; }
            for (int c = right - 1; c >= left; c--) { cellRow[size] = bottom; cellCol[size++] = c; }
            for (int r = bottom - 1; r > top; r--) { cellRow[size] = r; cellCol[size++] = left; }
            int shift = k % length; // 칸 수만큼 돌면 제자리로 돌아온다
            if (ring % 2 == 1) {
                shift = (length - shift) % length; // 반시계 방향으로 shift칸 = 시계 방향으로 length - shift칸(음수의 나머지를 피한다)
            }
            // 시계 방향으로 shift칸 돌면 i번째 칸의 보석은 i + shift번째 칸으로 간다
            for (int i = 0; i < length; i++) {
                int j = (i + shift) % length;
                result[cellRow[j]][cellCol[j]] = board[cellRow[i]][cellCol[i]];
            }
        }
        return result;
    }
}
