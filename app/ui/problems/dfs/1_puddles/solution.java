import java.util.*;

class Solution {
    public int solution(String[] floor) {
        int rows = floor.length, cols = floor[0].length();
        boolean[][] visited = new boolean[rows][cols];
        int[] dr = {-1, 1, 0, 0};
        int[] dc = {0, 0, -1, 1};
        int count = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (floor[r].charAt(c) != '#' || visited[r][c]) continue;
                // 아직 어느 웅덩이에도 들지 않은 물 칸: 새 웅덩이를 하나 세고, 이어진 칸을 모두 방문 표시한다
                count++;
                visited[r][c] = true;
                ArrayDeque<int[]> stack = new ArrayDeque<>();
                stack.push(new int[]{r, c});
                while (!stack.isEmpty()) {
                    int[] now = stack.pop();
                    for (int d = 0; d < 4; d++) {
                        int nextR = now[0] + dr[d], nextC = now[1] + dc[d];
                        if (nextR < 0 || nextR >= rows || nextC < 0 || nextC >= cols) continue; // 바닥 밖
                        if (floor[nextR].charAt(nextC) == '#' && !visited[nextR][nextC]) {
                            visited[nextR][nextC] = true;
                            stack.push(new int[]{nextR, nextC});
                        }
                    }
                }
            }
        }
        return count;
    }
}
