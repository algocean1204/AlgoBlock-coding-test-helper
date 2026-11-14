import java.util.*;

class Solution {
    public int solution(String[] building) {
        int rows = building.length, cols = building[0].length();
        int[] dr = {-1, 1, 0, 0};
        int[] dc = {0, 0, -1, 1};

        // 1. 불: 불이 난 칸을 모두 처음부터 큐에 넣고 한 번에 퍼뜨린다(여러 출발점 BFS)
        // fire[r][c]: 불이 (r, c)에 닿는 시각. -1은 불이 끝내 닿지 않는 칸
        int[][] fire = new int[rows][cols];
        for (int[] line : fire) Arrays.fill(line, -1);
        ArrayDeque<int[]> queue = new ArrayDeque<>();
        int startR = 0, startC = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                char ch = building[r].charAt(c);
                if (ch == 'F') {
                    fire[r][c] = 0;
                    queue.add(new int[]{r, c});
                } else if (ch == 'S') {
                    startR = r;
                    startC = c;
                }
            }
        }
        while (!queue.isEmpty()) {
            int[] cur = queue.poll();
            int r = cur[0], c = cur[1];
            for (int d = 0; d < 4; d++) {
                int nr = r + dr[d], nc = c + dc[d];
                if (nr >= 0 && nr < rows && nc >= 0 && nc < cols
                        && building[nr].charAt(nc) != '#' && fire[nr][nc] == -1) {
                    fire[nr][nc] = fire[r][c] + 1;
                    queue.add(new int[]{nr, nc});
                }
            }
        }

        // 2. 사람: 불보다 먼저 닿는 칸으로만 움직이는 BFS
        int[][] person = new int[rows][cols];
        for (int[] line : person) Arrays.fill(line, -1);
        person[startR][startC] = 0;
        queue.add(new int[]{startR, startC});
        while (!queue.isEmpty()) {
            int[] cur = queue.poll();
            int r = cur[0], c = cur[1];
            for (int d = 0; d < 4; d++) {
                int nr = r + dr[d], nc = c + dc[d];
                if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
                if (building[nr].charAt(nc) == '#' || person[nr][nc] != -1) continue;
                int arrive = person[r][c] + 1;
                if (fire[nr][nc] != -1 && fire[nr][nc] <= arrive) continue; // 불이 같은 분이나 더 일찍 닿는 칸은 못 들어간다
                if (building[nr].charAt(nc) == 'E') return arrive;
                person[nr][nc] = arrive;
                queue.add(new int[]{nr, nc});
            }
        }
        return -1;
    }
}
