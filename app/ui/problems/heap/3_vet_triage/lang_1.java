// 언어 함정: java.int_overflow @ "모든 동물이 기다린 시간의 합"
import java.util.Arrays;
import java.util.PriorityQueue;

class Solution {
    public long solution(int[][] patients) {
        int n = patients.length;
        int[][] arrivals = new int[n][]; // {도착 시각, 진료 시간, 위급도, 번호}
        for (int i = 0; i < n; i++) {
            arrivals[i] = new int[]{patients[i][0], patients[i][1], patients[i][2], i};
        }
        // 도착 시각 순으로 정렬한다
        Arrays.sort(arrivals, (a, b) -> Integer.compare(a[0], b[0]));
        // 도착한 동물: 위급도는 큰 것, 진료 시간은 짧은 것, 번호는 작은 것이 꼭대기에 오게 비교 기준을 준다
        PriorityQueue<int[]> waiting = new PriorityQueue<>((a, b) -> {
            if (a[2] != b[2]) return Integer.compare(b[2], a[2]);
            if (a[1] != b[1]) return Integer.compare(a[1], b[1]);
            return Integer.compare(a[3], b[3]);
        });
        int time = 0;
        int nextArrival = 0; // arrivals에서 아직 힙에 넣지 않은 첫 자리
        int total = 0;       // 기다린 시간의 합
        for (int count = 0; count < n; count++) {
            if (waiting.isEmpty() && arrivals[nextArrival][0] > time) {
                time = arrivals[nextArrival][0]; // 도착한 동물이 없으면 다음 동물이 올 때까지 건너뛴다
            }
            while (nextArrival < n && arrivals[nextArrival][0] <= time) {
                waiting.add(arrivals[nextArrival]);
                nextArrival++;
            }
            int[] pet = waiting.poll();
            total += time - pet[0];
            time += pet[1];
        }
        return total;
    }
}
