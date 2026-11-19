// 언어 함정: java.missing_key_null
import java.util.*;

class Solution {
    public int solution(String[] bracelets) {
        Map<String, Integer> count = new HashMap<>();  // 대표 키 → 그 디자인의 팔찌 수
        for (String beads : bracelets) {
            String flipped = new StringBuilder(beads).reverse().toString();  // 반대 방향으로 읽은 것
            List<String> views = new ArrayList<>();  // 이 팔찌가 적힐 수 있는 모든 모습
            for (int start = 0; start < beads.length(); start++) {
                views.add(beads.substring(start) + beads.substring(0, start));  // start번째 구슬부터 같은 방향으로
                views.add(flipped.substring(start) + flipped.substring(0, start));  // 뒤집어서 start번째 구슬부터
            }
            String key = Collections.min(views);  // 사전 순으로 가장 앞선 모습을 대표로: 디자인이 같으면 키도 같다
            count.put(key, count.get(key) + 1);
        }
        return Collections.max(count.values());
    }
}
