import java.util.*;

class Solution {
    public int solution(String[] names, int[] days, int limit) {
        Map<String, Integer> last = new HashMap<>();  // 손님 → 마지막으로 온 날
        Map<String, Integer> visits = new HashMap<>();  // 손님 → 서로 다른 날에 온 횟수
        Set<String> broken = new HashSet<>();  // 이웃한 두 날의 차이가 limit을 넘은 적이 있는 손님
        for (int i = 0; i < names.length; i++) {
            String name = names[i];
            int day = days[i];
            Integer before = last.get(name);
            if (before == null) {  // 처음 온 손님
                last.put(name, day);
                visits.put(name, 1);
            } else if (day != before) {  // 같은 날 다시 들어온 것은 새 방문이 아니다
                if (day - before > limit) {
                    broken.add(name);
                }
                last.put(name, day);  // 이제 이 날이 마지막으로 온 날이다
                visits.put(name, visits.get(name) + 1);
            }
        }

        int steady = 0;
        for (Map.Entry<String, Integer> entry : visits.entrySet()) {
            if (entry.getValue() >= 2 && !broken.contains(entry.getKey())) {
                steady++;
            }
        }
        return steady;
    }
}
