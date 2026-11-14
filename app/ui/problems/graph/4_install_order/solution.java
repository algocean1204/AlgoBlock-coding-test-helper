import java.util.*;

class Solution {
    public int[] solution(int n, int[][] rules) {
        List<List<Integer>> after = new ArrayList<>(); // after[a]: a를 설치해야 설치할 수 있는 패키지들
        for (int i = 0; i <= n; i++) after.add(new ArrayList<>());
        int[] waiting = new int[n + 1]; // waiting[b]: b보다 먼저 설치해야 하는데 아직 설치하지 않은 패키지 수(진입 차수)
        for (int[] r : rules) {
            after.get(r[0]).add(r[1]);
            waiting[r[1]]++;
        }

        PriorityQueue<Integer> ready = new PriorityQueue<>(); // 자바 기본 힙은 작은 것이 먼저 나온다
        for (int p = 1; p <= n; p++) {
            if (waiting[p] == 0) ready.add(p);
        }
        int[] order = new int[n];
        int count = 0;
        while (!ready.isEmpty()) {
            int pkg = ready.poll();
            order[count++] = pkg;
            for (int nxt : after.get(pkg)) {
                waiting[nxt]--;
                if (waiting[nxt] == 0) ready.add(nxt);
            }
        }

        if (count < n) return new int[0]; // 끝내 설치할 수 없는 패키지가 남았다: 규칙에 사이클이 있다
        return order;
    }
}
