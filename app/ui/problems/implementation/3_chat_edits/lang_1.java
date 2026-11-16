// 언어 함정: java.string_equals
import java.util.*;

class Solution {
    public String[] solution(String[] records) {
        // 첫 번째 훑기: 메시지마다 마지막 상태(보낸이, 마지막 내용, 고친 적 있는가, 지워졌는가)를 모은다
        List<String> order = new ArrayList<>();
        Map<String, String> sender = new HashMap<>();
        Map<String, String> text = new HashMap<>();
        Set<String> edited = new HashSet<>();
        Set<String> deleted = new HashSet<>();
        for (String record : records) {
            String[] words = record.split(" ");
            String number = words[1];
            if (words[0] == "SEND") {
                order.add(number);
                sender.put(number, words[2]);
                text.put(number, words[3]);
            } else if (words[0].equals("EDIT")) {
                text.put(number, words[2]);
                edited.add(number);
            } else {
                deleted.add(number);
            }
        }

        // 두 번째 훑기: 남은 메시지를 보낸 순서대로 보며, 바로 앞 줄과 보낸이가 같으면 그 줄에 붙인다
        List<StringBuilder> lines = new ArrayList<>();
        String lineSender = "";
        for (String number : order) {
            if (deleted.contains(number)) {
                continue;
            }
            String shown = text.get(number) + (edited.contains(number) ? "*" : "");
            if (!lines.isEmpty() && lineSender.equals(sender.get(number))) {
                lines.get(lines.size() - 1).append(" ").append(shown);
            } else {
                lines.add(new StringBuilder(sender.get(number) + ": " + shown));
                lineSender = sender.get(number);
            }
        }
        String[] answer = new String[lines.size()];
        for (int i = 0; i < lines.size(); i++) {
            answer[i] = lines.get(i).toString();
        }
        return answer;
    }
}
