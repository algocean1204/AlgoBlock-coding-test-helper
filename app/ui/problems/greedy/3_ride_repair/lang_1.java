// 언어 함정: java.int_overflow @ "기다림의 합"
import java.util.*;

class Solution {
    public long solution(int[] fix, int[] line, int walk) {
        int n = fix.length;
        Integer[] order = new Integer[n];
        for (int i = 0; i < n; i++) {
            order[i] = i;
        }
        // a 다음에 b를 고치면 b의 손님이 (fix[a] + walk) × line[b]만큼 더 기다리고,
        // b 다음에 a를 고치면 a의 손님이 (fix[b] + walk) × line[a]만큼 더 기다린다 → 작은 쪽 차례가 앞
        Arrays.sort(order, (a, b) -> Long.compare((long) (fix[a] + walk) * line[b], (long) (fix[b] + walk) * line[a]));

        long now = 0;  // 지금 시각
        int total = 0;  // 기다림의 합
        for (int k = 0; k < n; k++) {
            int ride = order[k];
            if (k > 0) {
                now += walk;  // 다음 놀이기구까지 걸어간다(첫 놀이기구는 걷지 않는다)
            }
            now += fix[ride];  // 이 놀이기구를 다 고친 시각
            total += now * line[ride];
        }
        return total;
    }
}
