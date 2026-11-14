import java.util.PriorityQueue

class Solution {
    fun solution(pickup: IntArray, minutes: IntArray, booked: IntArray): IntArray {
        val must = BooleanArray(pickup.size)  // 꼭 받아야 하는 주문인가
        for (b in booked) must[b] = true
        val order = pickup.indices.sortedBy { pickup[it] }  // 찾으러 오는 시각이 이른 주문부터
        // PriorityQueue는 기본이 최소 힙이라, 가장 긴 것을 꺼내려고 거꾸로 된 비교 기준을 준다
        val canDrop = PriorityQueue<Int>(compareByDescending { it })  // 되무를 수 있는 받은 주문의 만드는 시간
        var count = 0  // 받은 주문 수
        var total = 0L  // 받은 주문을 쉬지 않고 모두 만들면 끝나는 시각 (넘치지 않게 Long)
        for (i in order) {
            count++
            total += minutes[i]
            if (!must[i]) canDrop.add(minutes[i])
            while (total > pickup[i] && canDrop.isNotEmpty()) {  // 늦는다: 가장 오래 걸리는 것부터 되무른다
                total -= canDrop.poll()
                count--
            }
            if (total > pickup[i]) return intArrayOf(-1, -1)  // 꼭 받아야 하는 주문끼리도 지킬 수 없다
        }
        return intArrayOf(count, total.toInt())
    }
}
