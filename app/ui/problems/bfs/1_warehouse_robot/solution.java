import java.util.*;

class Solution {
    public int solution(String[] floor) {
        int rows = floor.length, cols = floor[0].length();
        int startR = 0, startC = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (floor[r].charAt(c) == 'S') { startR = r; startC = c; }
            }
        }
        // distance[r][c]: 출발 칸에서 (r, c)까지의 이동 횟수. -1은 아직 가 보지 않은 칸
        int[][] distance = new int[rows][cols];
        for (int[] line : distance) Arrays.fill(line, -1);
        distance[startR][startC] = 0;
        ArrayDeque<int[]> queue = new ArrayDeque<>();
        queue.add(new int[]{startR, startC});
        int[] dr = {-1, 1, 0, 0};
        int[] dc = {0, 0, -1, 1};
        while (!queue.isEmpty()) {
            int[] cur = queue.poll();
            int r = cur[0], c = cur[1];
            if (floor[r].charAt(c) == 'E') return distance[r][c];
            for (int d = 0; d < 4; d++) {
                int nr = r + dr[d], nc = c + dc[d];
                if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
                if (floor[nr].charAt(nc) == '#' || distance[nr][nc] != -1) continue;
                distance[nr][nc] = distance[r][c] + 1; // 넣을 때 바로 적어야 같은 칸이 두 번 들어가지 않는다
                queue.add(new int[]{nr, nc});
            }
        }
        return -1;
    }
}
