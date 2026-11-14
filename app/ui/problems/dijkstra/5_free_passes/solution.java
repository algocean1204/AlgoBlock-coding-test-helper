import java.util.*;

class Solution {
    public int solution(int n, int[][] roads, int k) {
        List<List<int[]>> graph = new ArrayList<>();
        for (int i = 0; i <= n; i++) graph.add(new ArrayList<>());
        for (int[] road : roads) {
            graph.get(road[0]).add(new int[]{road[1], road[2]});
            graph.get(road[1]).add(new int[]{road[0], road[2]});
        }

        // dist[city][used][just]: 통행권을 used장 쓰고 city에 왔을 때 낸 통행료 합의 최솟값(최대 약 1억6천만이라 int로 충분)
        // just는 바로 앞 도로에 통행권을 썼으면 1, 통행료를 냈으면(또는 아직 출발 전이면) 0
        int[][][] dist = new int[n + 1][k + 1][2];
        for (int[][] rows : dist) for (int[] row : rows) Arrays.fill(row, Integer.MAX_VALUE);
        dist[1][0][0] = 0;
        // 힙에는 {통행료 합, 도시, 쓴 통행권 수, 바로 앞에 썼는가}를 넣고 통행료가 작은 것부터 꺼낸다
        PriorityQueue<int[]> heap = new PriorityQueue<>((x, y) -> Integer.compare(x[0], y[0]));
        heap.add(new int[]{0, 1, 0, 0});
        while (!heap.isEmpty()) {
            int[] top = heap.poll();
            int cost = top[0], city = top[1], used = top[2], just = top[3];
            if (cost > dist[city][used][just]) continue;
            if (city == n) return cost;  // 몇 장을 썼든 n번 도시를 처음 꺼낸 값이 가장 싸다(통행권은 남겨도 된다)
            for (int[] edge : graph.get(city)) {
                int nxt = edge[0], toll = edge[1];
                if (cost + toll < dist[nxt][used][0]) {  // 통행료를 낸다
                    dist[nxt][used][0] = cost + toll;
                    heap.add(new int[]{cost + toll, nxt, used, 0});
                }
                if (used < k && just == 0 && cost < dist[nxt][used + 1][1]) {  // 통행권을 쓴다(바로 앞 도로에 쓰지 않았을 때만)
                    dist[nxt][used + 1][1] = cost;
                    heap.add(new int[]{cost, nxt, used + 1, 1});
                }
            }
        }
        return -1;
    }
}
