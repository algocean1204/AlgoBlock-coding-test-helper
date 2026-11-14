import java.util.*;

class Solution {
    // 할증 시간: 07:30 이상 09:30 미만, 17:00 이상 19:00 미만(분)
    static final int[][] RUSH = {{7 * 60 + 30, 9 * 60 + 30}, {17 * 60, 19 * 60}};

    static int toMinutes(String clock) {
        return Integer.parseInt(clock.substring(0, 2)) * 60 + Integer.parseInt(clock.substring(3));
    }

    static int rideFee(int start, int end, int perMinute) {
        // 탄 분마다 1분 요금, 할증 시간과 겹친 분은 1분 요금을 한 번 더
        int fee = (end - start) * perMinute;
        for (int[] rush : RUSH) {
            int overlap = Math.min(end, rush[1]) - Math.max(start, rush[0]);
            if (overlap > 0) {
                fee += overlap * perMinute;
            }
        }
        return fee;
    }

    public int[][] solution(String[] rides, int[] price, int gap) {
        int unlock = price[0], perMinute = price[1], dayMax = price[2];

        Map<String, Integer> total = new HashMap<>();  // 회원 → 그날 요금 합
        Map<String, Integer> lastEnd = new HashMap<>();  // 회원 → 바로 앞 기록의 끝 시각(분)
        for (String ride : rides) {
            String[] words = ride.split(" ");
            String member = words[0];
            int start = toMinutes(words[1]);
            int end = toMinutes(words[2]);
            int fee = rideFee(start, end, perMinute);
            // 같은 회원의 바로 앞 기록이 끝난 지 gap분 이하이면 이어 탄 것: 잠금 해제 요금이 없다
            if (!lastEnd.containsKey(member) || start - lastEnd.get(member) > gap) {
                fee += unlock;
            }
            total.put(member, total.getOrDefault(member, 0) + fee);
            lastEnd.put(member, end);
        }

        List<int[]> answer = new ArrayList<>();
        for (String member : total.keySet()) {
            answer.add(new int[]{Integer.parseInt(member), Math.min(total.get(member), dayMax)});  // 상한은 하루 합에 한 번
        }
        // 요금이 많은 회원부터, 같으면 번호가 작은 회원부터
        answer.sort((a, b) -> a[1] != b[1] ? Integer.compare(b[1], a[1]) : Integer.compare(a[0], b[0]));
        return answer.toArray(new int[0][]);
    }
}
