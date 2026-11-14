import java.util.Collections;
import java.util.PriorityQueue;

class Solution {
    public int solution(String[] records, int k) {
        // PriorityQueue는 최소 힙이다. 비교 기준을 거꾸로(reverseOrder) 주면 가장 느린 기록(k위)이 꼭대기에 온다
        PriorityQueue<Integer> fastest = new PriorityQueue<>(Collections.reverseOrder()); // 지금까지 가장 빠른 기록 k개
        int alerts = 0;
        for (String record : records) {
            String[] parts = record.split(":");
            int time = Integer.parseInt(parts[0]) * 60 + Integer.parseInt(parts[1]);
            if (fastest.size() < k) {
                alerts++;
                fastest.add(time);
            } else if (time < fastest.peek()) { // 지금 k위보다 빨라야 한다. 같으면 먼저 들어온 기록이 앞선다
                alerts++;
                fastest.poll();
                fastest.add(time);
            }
        }
        return alerts;
    }
}
