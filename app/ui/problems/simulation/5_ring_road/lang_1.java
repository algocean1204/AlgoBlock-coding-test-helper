// 언어 함정: java.int_overflow @ "t는 1 이상 1,000,000,000,000 이하"
import java.util.*;

class Solution {
    public long solution(String road, long t) {
        int n = road.length();
        Map<String, Integer> firstSeen = new HashMap<>(); // 도로 모습 → 그 모습이 처음 나온 시각(초)
        List<Long> passed = new ArrayList<>();            // passed[s] = 처음 s초 동안 결승선을 지나간 횟수
        passed.add(0L);
        String state = road;
        int second = 0;
        while (second < t && !firstSeen.containsKey(state)) {
            firstSeen.put(state, second);
            long crossed = (state.charAt(n - 1) == '>' && state.charAt(0) == '.') ? 1 : 0;
            // 1초가 시작될 때의 state만 보고 새 도로 newRoad에 적는다
            char[] newRoad = new char[n];
            Arrays.fill(newRoad, '.');
            for (int i = 0; i < n; i++) {
                if (state.charAt(i) == '>') {
                    int front = (i + 1) % n;
                    if (state.charAt(front) == '.') newRoad[front] = '>';
                    else newRoad[i] = '>';
                }
            }
            state = new String(newRoad);
            second++;
            passed.add(passed.get(passed.size() - 1) + crossed);
        }
        if (second == t) return passed.get((int) t);
        // second초의 모습이 start초에 이미 나왔다: start초부터 cycle초마다 같은 흐름이 되풀이된다
        int start = firstSeen.get(state);
        int cycle = second - start;
        long perCycle = passed.get(second) - passed.get(start);
        int full = (int) ((t - start) / cycle);
        int rest = (int) ((t - start) % cycle);
        return passed.get(start) + full * perCycle + (passed.get(start + rest) - passed.get(start));
    }
}
