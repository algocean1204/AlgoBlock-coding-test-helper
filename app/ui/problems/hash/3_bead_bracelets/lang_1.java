// 언어 함정: java.missing_key_null
import java.util.*;

class Solution {
    public int solution(String[] bracelets) {
        Map<String, Integer> count = new HashMap<>();  // 대표 키 → 그 디자인의 팔찌 수
        int best = 0;
        for (String beads : bracelets) {
            String flipped = new StringBuilder(beads).reverse().toString();  // 반대 방향으로 읽은 것
            String key = null;
            for (int start = 0; start < beads.length(); start++) {
                // start번째 구슬부터 같은 방향으로, 그리고 뒤집어서 읽은 모습
                String same = beads.substring(start) + beads.substring(0, start);
                String other = flipped.substring(start) + flipped.substring(0, start);
                if (key == null || same.compareTo(key) < 0) key = same;
                if (other.compareTo(key) < 0) key = other;
            }
            // 사전 순으로 가장 앞선 모습을 대표로: 디자인이 같으면 키도 같다
            int now = count.get(key) + 1;
            count.put(key, now);
            best = Math.max(best, now);
        }
        return best;
    }
}
