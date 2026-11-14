import java.util.*;

class Solution {
    public int solution(String[] routes, String start, String goal) {
        // 선착장 이름마다 0부터 번호를 매기고, 번호로 인접 목록을 만든다
        Map<String, Integer> id = new HashMap<>();
        List<List<int[]>> graph = new ArrayList<>();
        for (String route : routes) {
            String[] part = route.split(" ");
            for (int i = 0; i < 2; i++) {
                if (!id.containsKey(part[i])) {
                    id.put(part[i], id.size());
                    graph.add(new ArrayList<>());
                }
            }
            graph.get(id.get(part[0])).add(new int[]{id.get(part[1]), Integer.parseInt(part[2])});
        }

        int source = id.get(start), target = id.get(goal);
        int INF = Integer.MAX_VALUE;  // 최대 시간은 6천만 정도라 int로 충분하다
        int[] dist = new int[id.size()];
        Arrays.fill(dist, INF);
        dist[source] = 0;
        // 힙에는 {시간, 선착장 번호}를 넣고 시간이 작은 것부터 꺼낸다
        PriorityQueue<int[]> heap = new PriorityQueue<>((x, y) -> Integer.compare(x[0], y[0]));
        heap.add(new int[]{0, source});
        while (!heap.isEmpty()) {
            int[] top = heap.poll();
            int d = top[0], now = top[1];
            if (d > dist[now]) continue;  // 이미 더 빠른 시간으로 확정된 선착장
            if (now == target) return d;  // 도착점은 큐에서 꺼낼 때 확정된다
            for (int[] edge : graph.get(now)) {
                int nxt = edge[0], minutes = edge[1];
                if (d + minutes < dist[nxt]) {
                    dist[nxt] = d + minutes;
                    heap.add(new int[]{dist[nxt], nxt});
                }
            }
        }
        return -1;
    }
}
