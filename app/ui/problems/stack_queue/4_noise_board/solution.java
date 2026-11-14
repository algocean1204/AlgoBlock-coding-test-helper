import java.util.*;

class Solution {
    public int[] solution(int[][] logs, int window) {
        int n = logs.length;
        int[] answer = new int[n];
        Deque<int[]> candidates = new ArrayDeque<>(); // 아직 가장 큰 값이 될 수 있는 기록 {time, level}. 앞에서 뒤로 갈수록 level이 작다
        for (int k = 0; k < n; k++) {
            int time = logs[k][0];
            int level = logs[k][1];
            // 새 기록보다 작거나 같은 옛 기록은 다시는 가장 큰 값이 못 된다: 뒤에서 버린다
            while (!candidates.isEmpty() && candidates.peekLast()[1] <= level) {
                candidates.pollLast();
            }
            candidates.addLast(new int[]{time, level});
            // 창을 벗어난 오래된 기록은 앞에서 뺀다(여러 개일 수 있다). 방금 넣은 기록은 늘 창 안이라 덱이 비지 않는다
            while (candidates.peekFirst()[0] <= time - window) {
                candidates.pollFirst();
            }
            answer[k] = candidates.peekFirst()[1];
        }
        return answer;
    }
}
