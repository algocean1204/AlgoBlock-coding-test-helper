import java.util.*;

class Solution {
    public int solution(int[][] mine, int drill) {
        int rows = mine.length, cols = mine[0].length;
        int[] dr = {-1, 1, 0, 0};
        int[] dc = {0, 0, -1, 1};

        // 상태 = (행, 열, 지금까지 쓴 드릴 수). 같은 칸이라도 쓴 드릴 수가 다르면 다른 상태다
        // distance[r][c][used]: 그 상태까지의 최소 이동 횟수. -1은 아직 가 보지 않은 상태
        int[][][] distance = new int[rows][cols][drill + 1];
        for (int[][] plane : distance) for (int[] line : plane) Arrays.fill(line, -1);
        distance[0][0][0] = 0;
        ArrayDeque<int[]> queue = new ArrayDeque<>();
        queue.add(new int[]{0, 0, 0});
        while (!queue.isEmpty()) {
            int[] cur = queue.poll();
            int r = cur[0], c = cur[1], used = cur[2];
            if (r == rows - 1 && c == cols - 1) return distance[r][c][used];
            for (int d = 0; d < 4; d++) {
                int nr = r + dr[d], nc = c + dc[d];
                if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
                int nextUsed = used + mine[nr][nc]; // 바위 칸이면 드릴을 한 번 더 쓴다
                if (nextUsed > drill) continue;
                if (distance[nr][nc][nextUsed] != -1) continue;
                distance[nr][nc][nextUsed] = distance[r][c][used] + 1;
                queue.add(new int[]{nr, nc, nextUsed});
            }
        }
        return -1;
    }
}
