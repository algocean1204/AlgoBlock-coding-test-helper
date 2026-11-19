import java.util.*;

class Solution {
    public int solution(String expr) {
        Map<Character, Character> partner = Map.of(')', '(', ']', '[', '}', '{');
        Deque<Character> stack = new ArrayDeque<>();
        int deepest = 0;
        for (int k = 0; k < expr.length(); k++) {
            char ch = expr.charAt(k);
            if (ch == '(' || ch == '[' || ch == '{') {
                stack.push(ch);
                deepest = Math.max(deepest, stack.size());
            } else if (partner.containsKey(ch)) {
                char open = partner.get(ch);
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
