import java.util.*;

class Solution {
    public int solution(String start, String goal, String[] dictionary) {
        Set<String> words = new HashSet<>(Arrays.asList(dictionary));
        if (!words.contains(goal)) return -1;

        // steps: start에서 낱말을 만들기까지 바꾼 횟수. 들어 있으면 이미 큐에 넣은 낱말이다
        Map<String, Integer> steps = new HashMap<>();
        steps.put(start, 0);
        ArrayDeque<String> queue = new ArrayDeque<>();
        queue.add(start);
        while (!queue.isEmpty()) {
            String word = queue.poll();
            if (word.equals(goal)) return steps.get(word);
            char[] chars = word.toCharArray();
            for (int i = 0; i < chars.length; i++) {
                char original = chars[i];
                for (char ch = 'a'; ch <= 'z'; ch++) {
                    if (ch == original) continue;
                    chars[i] = ch; // 한 자리만 바꾼 이웃 후보를 직접 만든다
                    String candidate = new String(chars);
                    if (words.contains(candidate) && !steps.containsKey(candidate)) {
                        steps.put(candidate, steps.get(word) + 1);
                        queue.add(candidate);
                    }
                }
                chars[i] = original;
            }
        }
        return -1;
    }
}
