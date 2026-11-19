import java.util.*;
import java.util.function.UnaryOperator;

class Solution {
    public int solution(String[][] cables) {
        Map<String, String> parent = new HashMap<>(); // 정점이 이름(문자열)이라 맵을 쓴다

        // 재귀 대신 반복문: 긴 줄 입력에서 스택이 넘치지 않게
        UnaryOperator<String> find = x -> {
            if (!parent.containsKey(x)) parent.put(x, x);
            while (!parent.get(x).equals(x)) {
                parent.put(x, parent.get(parent.get(x))); // 경로 압축
                x = parent.get(x);
            }
            return x;
        };

        for (int i = 0; i < cables.length; i++) {
            String rootX = find.apply(cables[i][0]);
            String rootY = find.apply(cables[i][1]);
            if (rootX.equals(rootY)) {
                return i + 1; // 몇 번째 케이블인지는 1부터 센다
            }
            parent.put(rootY, rootX);
        }
        return -1;
    }
}
