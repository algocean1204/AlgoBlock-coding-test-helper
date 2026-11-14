import java.util.*;

class Solution {
    public String[] solution(String[] classes, int[][] medals) {
        int n = classes.length;
        // 반 번호(0..n-1)를 줄 세운다. 정렬 기준은 금 많은 순 → 은 많은 순 → 동 많은 순 → 이름 사전 순
        Integer[] order = new Integer[n];
        for (int i = 0; i < n; i++) order[i] = i;
        Arrays.sort(order, (a, b) -> {
            // 메달은 많은 쪽이 앞(내림차순)이라 b와 a의 자리를 바꿔 비교한다
            if (medals[a][0] != medals[b][0]) return Integer.compare(medals[b][0], medals[a][0]);
            if (medals[a][1] != medals[b][1]) return Integer.compare(medals[b][1], medals[a][1]);
            if (medals[a][2] != medals[b][2]) return Integer.compare(medals[b][2], medals[a][2]);
            return classes[a].compareTo(classes[b]); // 이름은 사전 순(오름차순). 소문자뿐이라 compareTo가 곧 사전 순이다
        });
        String[] answer = new String[n];
        for (int i = 0; i < n; i++) answer[i] = classes[order[i]];
        return answer;
    }
}
