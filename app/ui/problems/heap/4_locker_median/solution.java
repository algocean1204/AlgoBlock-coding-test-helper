import java.util.Collections;
import java.util.PriorityQueue;

class Solution {
    public long solution(int[] houses) {
        // PriorityQueue는 최소 힙이다. low는 비교 기준을 거꾸로(reverseOrder) 줘서 가장 큰 값이 꼭대기에 오게 한다
        PriorityQueue<Integer> low = new PriorityQueue<>(Collections.reverseOrder()); // 작은 쪽 절반
        PriorityQueue<Integer> high = new PriorityQueue<>();                          // 큰 쪽 절반. 가장 작은 값이 꼭대기
        // 거리 합은 int를 넘을 수 있어 모두 long으로 둔다
        long lowSum = 0L;
        long highSum = 0L;
        long total = 0L;
        for (int house : houses) {
            if (low.isEmpty() || house <= low.peek()) {
                low.add(house);
                lowSum += house;
            } else {
                high.add(house);
                highSum += house;
            }
            // 개수 맞추기: low가 high와 같거나 하나 더 많게 둔다. 그러면 low의 꼭대기가 가운데 값이다
            if (low.size() > high.size() + 1) {
                int moved = low.poll();
                lowSum -= moved;
                high.add(moved);
                highSum += moved;
            } else if (high.size() > low.size()) {
                int moved = high.poll();
                highSum -= moved;
                low.add(moved);
                lowSum += moved;
            }
            long middle = low.peek();
            // (작은 쪽 집들에서 가운데까지의 거리 합) + (큰 쪽 집들에서 가운데까지의 거리 합)
            total += (middle * low.size() - lowSum) + (highSum - middle * high.size());
        }
        return total;
    }
}
