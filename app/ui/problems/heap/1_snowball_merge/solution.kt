import java.util.PriorityQueue

class Solution {
    fun solution(snowballs: IntArray): Long {
        // PriorityQueue는 가장 작은 것이 꼭대기인 최소 힙이다. 합이 Int를 넘을 수 있어 Long으로 담는다
        val heap = PriorityQueue<Long>()
        for (snowball in snowballs) {
            heap.add(snowball.toLong())
        }
        var total = 0L
        while (heap.size > 1) {
            val lightest = heap.poll()
            val second = heap.poll()
            val merged = lightest + second
            total += merged
            heap.add(merged)
        }
        return total
    }
}
