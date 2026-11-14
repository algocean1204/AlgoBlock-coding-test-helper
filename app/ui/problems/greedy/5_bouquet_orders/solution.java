import java.util.*;

class Solution {
    public int[] solution(int[] pickup, int[] minutes, int[] booked) {
        int n = pickup.length;
        boolean[] must = new boolean[n];  // 꼭 받아야 하는 주문인가
        for (int b : booked) must[b] = true;
        Integer[] order = new Integer[n];
        for (int i = 0; i < n; i++) order[i] = i;
        Arrays.sort(order, (a, b) -> Integer.compare(pickup[a], pickup[b]));  // 찾으러 오는 시각이 이른 주문부터
        // PriorityQueue는 기본이 최소 힙이라, 가장 긴 것을 꺼내려고 거꾸로 된 비교 기준을 준다
        PriorityQueue<Integer> canDrop = new PriorityQueue<>(Collections.reverseOrder());  // 되무를 수 있는 받은 주문의 만드는 시간
        int count = 0;  // 받은 주문 수
        long total = 0;  // 받은 주문을 쉬지 않고 모두 만들면 끝나는 시각 (넘치지 않게 long)
        for (int i : order) {
            count++;
            total += minutes[i];
            if (!must[i]) canDrop.add(minutes[i]);
            while (total > pickup[i] && !canDrop.isEmpty()) {  // 늦는다: 가장 오래 걸리는 것부터 되무른다
                total -= canDrop.poll();
                count--;
            }
            if (total > pickup[i]) return new int[]{-1, -1};  // 꼭 받아야 하는 주문끼리도 지킬 수 없다
        }
        return new int[]{count, (int) total};
    }
}
