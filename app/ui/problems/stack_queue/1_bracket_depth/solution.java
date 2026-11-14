import java.util.*;

class Solution {
    public int solution(String expr) {
        Deque<Character> stack = new ArrayDeque<>();
        int deepest = 0;
        for (int k = 0; k < expr.length(); k++) {
            char ch = expr.charAt(k);
            if (ch == '(' || ch == '[' || ch == '{') {
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
