import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

class Solution {
    public int solution(String tiles, int m) {
        Set<Integer> numbers = new HashSet<>();
        class Orders {
            // 순열 도구가 없어서 직접 만든다: rest에서 length장을 골라 늘어놓는 모든 줄
            List<String> permutations(String rest, int length) {
                List<String> out = new ArrayList<>();
                if (length == 0) {
                    out.add("");
                    return out;
                }
                for (int i = 0; i < rest.length(); i++) {
                    for (String tail : permutations(rest.substring(0, i) + rest.substring(i + 1), length - 1)) {
                        out.add(rest.charAt(i) + tail);
                    }
                }
                return out;
            }
        }
        Orders orders = new Orders();
        for (int length = 2; length <= tiles.length(); length++) { // 두 장 이상
            for (String order : orders.permutations(tiles, length)) {
                if (order.charAt(0) == '0') { // 맨 앞에 0 타일은 놓을 수 없다
                    continue;
                }
                numbers.add(Integer.parseInt(order)); // 같은 수는 집합이 한 번만 남긴다(최대 8자리라 int로 충분하다)
            }
        }
        int count = 0;
        for (int x : numbers) {
            if (x % m == 0) {
                count++;
            }
        }
        return count;
    }
}
