import java.util.*;

class Solution {
    public String[] solution(String[] loans, int k) {
        Map<String, Integer> count = new HashMap<>();  // 제목마다 지금까지 빌려진 횟수
        List<String> shelf = new ArrayList<>();  // 추천 서가에 꽂힌 차례대로
        for (String title : loans) {
            int now = count.getOrDefault(title, 0) + 1;
            count.put(title, now);
            if (now == k) {  // 바로 지금 k번째로 빌려졌다
                shelf.add(title);
            }
        }
        return shelf.toArray(new String[0]);
    }
}
