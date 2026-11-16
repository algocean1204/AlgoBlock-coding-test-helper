// 언어 함정: java.missing_key_null
import java.util.*;

class Solution {
    public long solution(int[] presses, int m) {
        // 조명 상태를 정수 하나로 담는다: k번 조명이 켜져 있으면 (k - 1)번째 비트가 1
        Map<Integer, Integer> seen = new HashMap<>();  // 상태 → 지금까지 그 상태가 나온 횟수
        seen.put(0, 1);  // 아무것도 누르지 않은 처음(모두 꺼짐)도 한 번
        int state = 0;
        long total = 0;  // 토막 수는 int를 넘을 수 있다
        for (int button : presses) {
            if (button == 0) {
                state = 0;  // 모두 끈다
            } else {
                state ^= 1 << (button - 1);  // 그 조명만 뒤집는다
            }
            // 앞서 지금과 같은 상태였던 때마다, 그 다음 버튼부터 지금 버튼까지가 제자리 토막이다
            int before = seen.get(state);
            total += before;
            seen.put(state, before + 1);
        }
        return total;
    }
}
