import java.util.PriorityQueue

class Solution {
    fun solution(houses: IntArray): Long {
        // PriorityQueue는 최소 힙이다. low는 비교 기준을 거꾸로(compareByDescending) 줘서 가장 큰 값이 꼭대기에 오게 한다
        val low = PriorityQueue<Int>(compareByDescending { it }) // 작은 쪽 절반
        val high = PriorityQueue<Int>()                          // 큰 쪽 절반. 가장 작은 값이 꼭대기
        // 거리 합은 Int를 넘을 수 있어 모두 Long으로 둔다
        var lowSum = 0L
        var highSum = 0L
        var total = 0L
        for (house in houses) {
            if (low.isEmpty() || house <= low.peek()) {
                low.add(house)
                lowSum += house
            } else {
                high.add(house)
                highSum += house
            }
            // 개수 맞추기: low가 high와 같거나 하나 더 많게 둔다. 그러면 low의 꼭대기가 가운데 값이다
            if (low.size > high.size + 1) {
                val moved = low.poll()
                lowSum -= moved
                high.add(moved)
                highSum += moved
            } else if (high.size > low.size) {
                val moved = high.poll()
                highSum -= moved
                low.add(moved)
                lowSum += moved
            }
            val middle = low.peek().toLong()
            // (작은 쪽 집들에서 가운데까지의 거리 합) + (큰 쪽 집들에서 가운데까지의 거리 합)
            total += (middle * low.size - lowSum) + (highSum - middle * high.size)
        }
        return total
    }
}
