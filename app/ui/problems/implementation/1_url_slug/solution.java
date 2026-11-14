import java.util.*;

class Solution {
    public String solution(String title, String[] taken) {
        List<String> skip = Arrays.asList("a", "an", "the", "of", "and");

        // 1~2. 빈칸으로 나누고, 낱말마다 소문자로 바꿔 영문 소문자·숫자만 남긴다. 다 지워진 낱말은 뺀다
        List<String> words = new ArrayList<>();
        for (String word : title.split(" ")) {
            StringBuilder kept = new StringBuilder();
            for (char ch : word.toLowerCase().toCharArray()) {
                if ((ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9')) {
                    kept.append(ch);
                }
            }
            if (kept.length() > 0) {
                words.add(kept.toString());
            }
        }

        // 3. 규칙 3의 낱말 빼기. 다 빠져 목록이 비면 빼지 않는다
        List<String> left = new ArrayList<>();
        for (String word : words) {
            if (!skip.contains(word)) {
                left.add(word);
            }
        }
        if (!left.isEmpty()) {
            words = left;
        }

        // 4. 낱말 단위로 이어 붙이다가 길이가 24를 넘게 되면 멈춘다
        String first = words.get(0);
        String slug = first.length() > 24 ? first.substring(0, 24) : first;
        for (int i = 1; i < words.size(); i++) {
            if (slug.length() + 1 + words.get(i).length() > 24) {
                break;
            }
            slug = slug + "-" + words.get(i);
        }

        // 5. taken에 있으면 -2, -3, … 을 붙여 본다
        Set<String> used = new HashSet<>(Arrays.asList(taken));
        if (!used.contains(slug)) {
            return slug;
        }
        int number = 2;
        while (used.contains(slug + "-" + number)) {
            number++;
        }
        return slug + "-" + number;
    }
}
