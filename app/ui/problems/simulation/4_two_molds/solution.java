class Solution {
    private int n, m;

    // grid에서 (r, c)와 맞닿은 칸 가운데 mold인 칸의 수
    private int count(char[][] grid, int r, int c, char mold) {
        int[] dr = {-1, 1, 0, 0};
        int[] dc = {0, 0, -1, 1};
        int total = 0;
        for (int d = 0; d < 4; d++) {
            int nr = r + dr[d], nc = c + dc[d];
            if (nr >= 0 && nr < n && nc >= 0 && nc < m && grid[nr][nc] == mold) total++;
        }
        return total;
    }

    public String[] solution(String[] dish, int hours) {
        n = dish.length;
        m = dish[0].length();
        char[][] board = new char[n][];
        for (int r = 0; r < n; r++) board[r] = dish[r].toCharArray();
        for (int hour = 0; hour < hours; hour++) {
            // 1단계(번식): 1시간이 시작될 때의 board를 보고, 결과는 grown에 적는다
            char[][] grown = new char[n][];
            for (int r = 0; r < n; r++) grown[r] = board[r].clone();
            for (int r = 0; r < n; r++) {
                for (int c = 0; c < m; c++) {
                    if (board[r][c] != '.') continue;
                    int a = count(board, r, c, 'A'), b = count(board, r, c, 'B');
                    if (a > b) grown[r][c] = 'A';
                    else if (b > a) grown[r][c] = 'B';
                    else if (a > 0) grown[r][c] = '#';
                }
            }
            // 2단계(포위): 1단계가 끝난 grown을 보고, 결과는 result에 적는다
            char[][] result = new char[n][];
            for (int r = 0; r < n; r++) result[r] = grown[r].clone();
            for (int r = 0; r < n; r++) {
                for (int c = 0; c < m; c++) {
                    if (grown[r][c] == 'A' && count(grown, r, c, 'B') >= 3) result[r][c] = '#';
                    else if (grown[r][c] == 'B' && count(grown, r, c, 'A') >= 3) result[r][c] = '#';
                }
            }
            boolean same = true; // 1시간 동안 아무것도 바뀌지 않았으면 그 뒤로도 계속 같다
            for (int r = 0; r < n; r++) {
                if (!java.util.Arrays.equals(result[r], board[r])) same = false;
            }
            if (same) break;
            board = result;
        }
        String[] answer = new String[n];
        for (int r = 0; r < n; r++) answer[r] = new String(board[r]);
        return answer;
    }
}
