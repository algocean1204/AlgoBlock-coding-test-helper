import java.util.PriorityQueue

class Solution {
    fun solution(records: Array<String>, k: Int): Int {
        // PriorityQueue는 최소 힙이다. 비교 기준을 거꾸로(reverseOrder) 주면 가장 느린 기록(k위)이 꼭대기에 온다
        val fastest = PriorityQueue<Int>(compareByDescending { it }) // 지금까지 가장 빠른 기록 k개
        var alerts = 0
        for (record in records) {
            val parts = record.split(":")
            val time = parts[0].toInt() * 60 + parts[1].toInt()
            if (fastest.size < k) {
                alerts++
                fastest.add(time)
            } else if (time < fastest.peek()) { // 지금 k위보다 빨라야 한다. 같으면 먼저 들어온 기록이 앞선다
                alerts++
                fastest.poll()
                fastest.add(time)
            }
        }
        return alerts
    }
}
