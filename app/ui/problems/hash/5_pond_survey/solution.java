import java.util.*;

class Solution {
    public int[] solution(String[] log) {
        Map<String, Map<String, Integer>> count = new HashMap<>();  // 구역 → {종 → 마릿수}. 1마리 이상인 종만 둔다
        Map<String, Integer> zonesOf = new HashMap<>();  // 종 → 그 종이 1마리 이상 있는 구역 수
        List<Integer> answers = new ArrayList<>();
        for (String line : log) {
            String[] words = line.split(" ");
            if (words[0].equals("see")) {
                String zone = words[1], kind = words[2];
                int n = Integer.parseInt(words[3]);
                Map<String, Integer> inZone = count.computeIfAbsent(zone, key -> new HashMap<>());
                int before = inZone.getOrDefault(kind, 0);  // 덮어쓰기 전에 지금 값을 본다
                // 종의 구역 수는 없음 → 있음, 있음 → 없음으로 바뀔 때만 달라진다
                if (before == 0 && n > 0) {
                    zonesOf.put(kind, zonesOf.getOrDefault(kind, 0) + 1);
                }
                if (before > 0 && n == 0) {
                    zonesOf.put(kind, zonesOf.get(kind) - 1);
                }
                if (n > 0) {
                    inZone.put(kind, n);  // 더하지 않고 바꾼다
                } else {
                    inZone.remove(kind);  // 0마리는 지운다: 구역의 종 수 = 안쪽 표의 크기
                }
            } else if (words[0].equals("zone")) {
                Map<String, Integer> inZone = count.get(words[1]);
                answers.add(inZone == null ? 0 : inZone.size());
            } else {
                answers.add(zonesOf.getOrDefault(words[1], 0));
            }
        }
        int[] result = new int[answers.size()];
        for (int i = 0; i < result.length; i++) {
            result[i] = answers.get(i);
        }
        return result;
    }
}
