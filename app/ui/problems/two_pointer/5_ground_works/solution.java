class Solution {
    public int solution(int rows, int cols, int[][] works) {
        // 끝 다음 칸(r2 + 1행, c2 + 1열)에도 표시해야 하므로 한 행, 한 열씩 크게 만든다
        int[][] diff = new int[rows + 1][cols + 1];
        for (int[] work : works) {
            int r1 = work[0], c1 = work[1], r2 = work[2], c2 = work[3], amount = work[4];
            diff[r1][c1] += amount;
            diff[r1][c2 + 1] -= amount;
            diff[r2 + 1][c1] -= amount;
            diff[r2 + 1][c2 + 1] += amount;
        }
        // 가로로 누적: 같은 행 안에서 왼쪽 표시를 오른쪽으로 펼친다
        for (int r = 0; r <= rows; r++) {
            for (int c = 1; c <= cols; c++) {
                diff[r][c] += diff[r][c - 1];
            }
        }
        // 세로로 누적: 같은 열 안에서 위쪽 표시를 아래로 펼친다
        for (int r = 1; r <= rows; r++) {
            for (int c = 0; c <= cols; c++) {
                diff[r][c] += diff[r - 1][c];
            }
        }
        // 값이 최대 3만 × 1,000 = 3천만이라 int로 충분하다
        int count = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (diff[r][c] == 0) {
                    count++;
                }
            }
        }
        return count;
    }
}
