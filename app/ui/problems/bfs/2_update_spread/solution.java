import java.util.*;

class Solution {
    public int[] solution(int n, int[][] cables, int start, int[] offline) {
        List<List<Integer>> neighbors = new ArrayList<>();
        for (int i = 0; i <= n; i++) neighbors.add(new ArrayList<>());
        for (int[] cable : cables) {
            neighbors.get(cable[0]).add(cable[1]); // 케이블은 양쪽 방향이다
            neighbors.get(cable[1]).add(cable[0]);
        }
        boolean[] off = new boolean[n + 1]; // off[v]: v번 서버가 꺼져 있는가
        for (int server : offline) off[server] = true;

        // minute[v]: v번 서버가 파일을 받는 시각. -1은 아직(또는 끝내) 받지 못한 서버
        int[] minute = new int[n + 1];
        Arrays.fill(minute, -1);
        minute[start] = 0;
        ArrayDeque<Integer> queue = new ArrayDeque<>();
        queue.add(start);
        while (!queue.isEmpty()) {
            int server = queue.poll();
            for (int next : neighbors.get(server)) {
                if (minute[next] == -1 && !off[next]) { // 꺼진 서버는 받지도 보내지도 않는다
                    minute[next] = minute[server] + 1;
                    queue.add(next);
                }
            }
        }
        int latest = -1; // start번 서버가 0분이라 받지 못한 서버(-1)는 가장 큰 값이 되지 않는다
        for (int v : minute) latest = Math.max(latest, v);
        int count = 0;
        for (int v : minute) if (v == latest) count++;
        return new int[]{latest, count};
    }
}
