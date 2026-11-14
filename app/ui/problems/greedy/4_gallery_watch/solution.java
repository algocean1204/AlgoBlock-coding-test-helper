import java.util.*;

class Solution {
    public int solution(int[][] helpers, int close, int gap) {
        int[][] people = helpers.clone();
        Arrays.sort(people, (a, b) -> Integer.compare(a[0], b[0]));  // 오는 시각이 이른 사람부터
        long reach = 0;  // 시각 0부터 reach까지는 빈 시간이 모두 gap 이하다
        long best = 0;  // 지금까지 본 '불러야 오는 사람' 가운데 가장 늦게 떠나는 시각
        int called = 0;
        int i = 0;
        // reach + gap은 20억에 이를 수 있어 long으로 계산한다
        while (close - reach > gap) {  // 남은 시간을 비워 둘 수 없다: 누군가 더 있어야 한다
            // reach + gap 이전에 오는 사람은 지금 이어 받을 수 있다
            while (i < people.length && people[i][0] <= reach + gap) {
                if (people[i][2] == 1) {
                    reach = Math.max(reach, people[i][1]);  // 약속한 사람은 부르지 않아도 온다: 끝을 먼저 늘린다
                } else {
                    best = Math.max(best, people[i][1]);
                }
                i++;
            }
            if (close - reach <= gap) {
                break;
            }
            if (best <= reach) {
                return -1;  // 누구를 불러도 reach + gap 안에 이어 받아 더 멀리 갈 수 없다
            }
            reach = best;  // 이어 받을 수 있는 사람 가운데 가장 늦게 떠나는 사람을 부른다
            called++;
        }
        return called;
    }
}
