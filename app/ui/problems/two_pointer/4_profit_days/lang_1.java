// 언어 함정: java.int_overflow @ "모두 몇 개인지"
import java.util.HashMap;

class Solution {
    public long solution(int[] profits, int target) {
        // seen.get(s): 지금까지 나온 누적 합 가운데 값이 s인 것의 개수
        // 아무 날도 더하지 않은 누적 합 0을 한 번 넣어 두어야 첫째 날부터 시작하는 기간도 센다
        HashMap<Long, Integer> seen = new HashMap<>();
        seen.put(0L, 1);
        long total = 0;
        int count = 0;
        for (int profit : profits) {
            total += profit;
            // 앞쪽 누적 합이 total - target이었다면, 그다음 날부터 오늘까지의 합이 target이다
            // getOrDefault: 키가 없으면 0을 돌려준다
            count += seen.getOrDefault(total - target, 0);
            seen.put(total, seen.getOrDefault(total, 0) + 1);
        }
        return count;
    }
}
