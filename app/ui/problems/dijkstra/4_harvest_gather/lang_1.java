// 언어 함정: java.int_overflow @ "1 ≤ fast ≤ slow ≤ 100,000,000"
import java.util.*;

class Solution {
    private static final long INF = Long.MAX_VALUE / 4;  // 시간 합이 int를 넘으므로 long, 더해도 넘치지 않게 넉넉히

    private long[] dijkstra(List<List<long[]>> graph, int n, int start) {
        long[] dist = new long[n + 1];
        Arrays.fill(dist, INF);
        dist[start] = 0;
        PriorityQueue<long[]> heap = new PriorityQueue<>((a, b) -> Long.compare(a[0], b[0]));
        heap.add(new long[]{0, start});
        while (!heap.isEmpty()) {
            long[] top = heap.poll();
            int d = (int) top[0];
            int now = (int) top[1];
            if (d > dist[now]) {
                continue;
            }
            for (long[] edge : graph.get(now)) {
                int nxt = (int) edge[0];
                if (d + edge[1] < dist[nxt]) {
                    dist[nxt] = d + edge[1];
                    heap.add(new long[]{dist[nxt], nxt});
                }
            }
        }
        return dist;
    }

    public long solution(int n, int[][] roads, int[] farms, int market) {
        List<List<long[]>> small = new ArrayList<>();  // 작은 트럭: u → v, slow분
        List<List<long[]>> bigBack = new ArrayList<>();  // 큰 트럭의 도로를 거꾸로 뒤집은 것: v → u, fast분
        for (int i = 0; i <= n; i++) {
            small.add(new ArrayList<>());
            bigBack.add(new ArrayList<>());
        }
        for (int[] r : roads) {
            small.get(r[0]).add(new long[]{r[1], r[2]});
            bigBack.get(r[1]).add(new long[]{r[0], r[3]});
        }

        // 뒤집은 그래프에서 시장으로부터의 거리 = 각 마을에서 시장까지 큰 트럭이 걸리는 시간
        long[] toMarket = dijkstra(bigBack, n, market);

        long[] gather = new long[n + 1];  // gather[m]: 작은 트럭이 모두 m번 마을에 모이는 시각(가장 늦게 도착한 트럭)
        for (int farm : farms) {
            long[] arrive = dijkstra(small, n, farm);
            for (int m = 1; m <= n; m++) {
                gather[m] = Math.max(gather[m], arrive[m]);
            }
        }

        long answer = INF;
        for (int m = 1; m <= n; m++) {  // 모이는 마을을 모두 해 본다. 닿지 못하는 곳은 무한대라 뽑히지 않는다
            if (gather[m] < INF && toMarket[m] < INF) {
                answer = Math.min(answer, gather[m] + toMarket[m]);
            }
        }
        return answer < INF ? answer : -1;
    }
}
