import java.util.*;

class Solution {
    public int[] solution(int rows, int[][] apples, int k) {
        List<Set<Integer>> kindsOf = new ArrayList<>();  // kindsOf.get(줄 번호) = 그 줄의 서로 다른 무게(0번 칸은 쓰지 않는다)
        for (int row = 0; row <= rows; row++) {
            kindsOf.add(new HashSet<>());
        }
        for (int[] apple : apples) {
            kindsOf.get(apple[0]).add(apple[1]);  // 같은 무게는 한 번만
        }

        int[] answer = new int[rows];
        for (int row = 1; row <= rows; row++) {
            List<Integer> kinds = new ArrayList<>(kindsOf.get(row));
            kinds.sort(Collections.reverseOrder());  // 무거운 것부터
            // k번째 무게는 위치 k-1. 적은 무게가 k개보다 적으면 -1(사과가 없는 줄 포함)
            answer[row - 1] = k <= kinds.size() ? kinds.get(k - 1) : -1;
        }
        return answer;
    }
}
