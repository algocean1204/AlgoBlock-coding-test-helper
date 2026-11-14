import java.util.*;

class Solution {
    public int solution(String[] kinds, int[] minutes, int time) {
        // 모양마다 그 도장을 받는 가장 짧은 시간만 남긴다(같은 모양은 한 칸만 채우므로)
        Map<String, Integer> shortest = new HashMap<>();
        for (int i = 0; i < kinds.length; i++) {
            Integer before = shortest.get(kinds[i]);
            if (before == null || minutes[i] < before) {
                shortest.put(kinds[i], minutes[i]);
            }
        }
        int[] sorted = new int[shortest.size()];
        int k = 0;
        for (int minute : shortest.values()) {
            sorted[k++] = minute;
        }
        Arrays.sort(sorted);  // 짧은 것부터

        long used = 0;  // 지금까지 쓴 시간
        int filled = 0;  // 채운 칸 수
        for (int minute : sorted) {
            if (used + minute > time) {
                break;  // 이것이 안 들어가면 뒤의 더 긴 것도 안 들어간다
            }
            used += minute;
            filled++;
        }
        return filled;
    }
}
