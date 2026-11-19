import java.util.*;

class Solution {
    public String[] solution(String[] classes, int[][] medals) {
        List<int[]> rows = new ArrayList<>();
        for (int i = 0; i < classes.length; i++) {
            int gold = medals[i][0], silver = medals[i][1], bronze = medals[i][2];
            // 메달은 많은 쪽이 앞(내림차순)이라 마이너스를 붙이고, 이름은 사전 순(오름차순)으로 견주도록 반 번호를 함께 둔다
            rows.add(new int[]{-gold, -silver, -bronze, i});
        }
        // 앞 칸부터 비교하고, 같으면 다음 칸으로 넘어간다. 마지막은 반 이름의 사전 순(소문자뿐이라 compareTo가 곧 사전 순이다)
        rows.sort(Comparator.<int[]>comparingInt(row -> row[0]).thenComparingInt(row -> row[1]).thenComparingInt(row -> row[2]).thenComparing(row -> classes[row[3]]));
        String[] answer = new String[rows.size()];
        for (int k = 0; k < rows.size(); k++) answer[k] = classes[rows.get(k)[3]];
        return answer;
    }
}
