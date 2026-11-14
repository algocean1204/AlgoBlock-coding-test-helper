import java.util.*;

class Solution {
    public int solution(int[][] ground) {
        int rows = ground.length, cols = ground[0].length;
        int[][] highest = new int[rows][cols];  // 그 칸까지 가는 길에서 넘는 가장 높은 턱의 최솟값
        for (int[] row : highest) Arrays.fill(row, Integer.MAX_VALUE);
        highest[0][0] = 0;
        // 힙에는 {턱 높이, 행, 열}을 넣고 턱이 낮은 것부터 꺼낸다
        PriorityQueue<int[]> heap = new PriorityQueue<>((x, y) -> Integer.compare(x[0], y[0]));
        heap.add(new int[]{0, 0, 0});
        int[] dr = {-1, 1, 0, 0};
        int[] dc = {0, 0, -1, 1};
        while (!heap.isEmpty()) {
            int[] top = heap.poll();
            int h = top[0], r = top[1], c = top[2];
            if (h > highest[r][c]) continue;
            if (r == rows - 1 && c == cols - 1) return h;
            for (int k = 0; k < 4; k++) {
                int nr = r + dr[k], nc = c + dc[k];
                if (nr >= 0 && nr < rows && nc >= 0 && nc < cols) {
                    int ledge = Math.abs(ground[nr][nc] - ground[r][c]);
                    int cur = Math.max(h, ledge);  // 합이 아니라 가장 높은 턱
                    if (cur < highest[nr][nc]) {
                        highest[nr][nc] = cur;
                        heap.add(new int[]{cur, nr, nc});
                    }
                }
            }
        }
        return highest[rows - 1][cols - 1];
    }
}
