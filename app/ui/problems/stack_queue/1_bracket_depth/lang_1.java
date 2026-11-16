// 언어 함정: java.string_equals
import java.util.*;

class Solution {
    public int solution(String expr) {
        Deque<Character> stack = new ArrayDeque<>();
        int deepest = 0;
        for (int k = 0; k < expr.length(); k++) {
            char ch = expr.charAt(k);
            if (expr.substring(k, k + 1) == "(" || ch == '[' || ch == '{') {
                stack.push(ch);
                deepest = Math.max(deepest, stack.size());
            } else if (ch == ')' || ch == ']' || ch == '}') {
                char open = ch == ')' ? '(' : (ch == ']' ? '[' : '{');
                if (stack.isEmpty() || stack.peek() != open) {
                    return -1;
                }
                stack.pop();
            }
        }
        if (!stack.isEmpty()) {
            return -1;
        }
        return deepest;
    }
}
