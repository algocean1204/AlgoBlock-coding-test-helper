// 언어 함정: java.int_overflow @ "힘의 합"
import java.util.PriorityQueue;

class Solution {
    public long solution(int[] snowballs) {
        // PriorityQueue는 가장 작은 것이 꼭대기인 최소 힙이다. 합이 int를 넘을 수 있어 long으로 담는다
        PriorityQueue<Long> heap = new PriorityQueue<>();
        for (int snowball : snowballs) {
            heap.add((long) snowball);
        }
        int total = 0;
        while (heap.size() > 1) {
            long lightest = heap.poll();
            long second = heap.poll();
            long merged = lightest + second;
            total += merged;
            heap.add(merged);
        }
        return total;
    }
}
