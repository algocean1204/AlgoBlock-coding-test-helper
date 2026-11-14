import java.util.*;

class Solution {
    public int[] solution(int n, int[][] roads) {
        List<List<int[]>> graph = new ArrayList<>();
        for (int i = 0; i <= n; i++) graph.add(new ArrayList<>());
        for (int[] road : roads) {
            graph.get(road[0]).add(new int[]{road[1], road[2]});
            graph.get(road[1]).add(new int[]{road[0], road[2]});
        }

        int INF = Integer.MAX_VALUE;  // 최대 시간은 약 6억이라 int로 충분하다
        int[] dist = new int[n + 1];
        Arrays.fill(dist, INF);
        dist[1] = 0;
        // 힙에는 {시간, 마을}을 넣고, 시간이 작은 것부터 꺼내도록 비교 기준을 준다
        PriorityQueue<int[]> heap = new PriorityQueue<>((x, y) -> Integer.compare(x[0], y[0]));
        heap.add(new int[]{0, 1});
        while (!heap.isEmpty()) {
            int[] top = heap.poll();
            int d = top[0], now = top[1];
            if (d > dist[now]) continue;  // 이미 더 짧은 시간으로 확정된 마을
            for (int[] edge : graph.get(now)) {
                int nxt = edge[0], time = edge[1];
                if (d + time < dist[nxt]) {
                    dist[nxt] = d + time;
                    heap.add(new int[]{dist[nxt], nxt});
                }
            }
        }
        return Arrays.copyOfRange(dist, 1, n + 1);
    }
}
