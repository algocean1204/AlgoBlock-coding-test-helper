import java.util.*;

class Solution {
    public int[] solution(int n, int[][] tracks, int[][] queries) {
        final long INF = 1_000_000_000L; // 가장 긴 최단 시간(299,000)보다 크고, 두 번 더해도 넘치지 않게 long으로 둔다
        long[][] dist = new long[n + 1][n + 1];
        for (long[] row : dist) Arrays.fill(row, INF);
        for (int s = 1; s <= n; s++) dist[s][s] = 0;
        for (int[] t : tracks) {
            if (t[2] < dist[t[0]][t[1]]) { // 같은 두 역 사이 선로가 여럿이면 짧은 것만 남긴다
                dist[t[0]][t[1]] = t[2];
                dist[t[1]][t[0]] = t[2];
            }
        }

        List<List<Integer>> asked = new ArrayList<>(); // asked[k]: k번 역까지 열렸을 때를 묻는 질문의 번호들
        for (int i = 0; i <= n; i++) asked.add(new ArrayList<>());
        for (int i = 0; i < queries.length; i++) asked.get(queries[i][0]).add(i);

        int[] answer = new int[queries.length];
        for (int k = 1; k <= n; k++) {
            // 플로이드: k번 역을 거쳐 가는 길로 모든 두 역 사이 거리를 고친다(아직 닫힌 역까지의 거리도 고쳐 둔다)
            for (int i = 1; i <= n; i++) {
                for (int j = 1; j <= n; j++) {
                    if (dist[i][k] + dist[k][j] < dist[i][j]) {
                        dist[i][j] = dist[i][k] + dist[k][j];
                    }
                }
            }
            // 이제 dist[a][b]는 1~k번 역만 거쳐 가는 가장 짧은 시간이다
            for (int idx : asked.get(k)) {
                long d = dist[queries[idx][1]][queries[idx][2]];
                answer[idx] = d >= INF ? -1 : (int) d;
            }
        }
        return answer;
    }
}
