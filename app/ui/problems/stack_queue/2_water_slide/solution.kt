import java.util.ArrayDeque

class Solution {
    fun solution(arrive: IntArray, ride: Int, gap: Int, cap: Int): Int {
        val sliding = ArrayDeque<Int>() // 미끄럼틀 안에 있는 사람이 벗어나는 시각. 먼저 출발한 사람이 앞
        var nextPerson = 0  // 줄의 맨 앞 사람 번호
        var lastStart = -1  // 바로 앞사람이 출발한 시각(아직 아무도 출발하지 않았으면 -1)
        var total = 0
        var time = 0
        while (nextPerson < arrive.size) {
            while (sliding.isNotEmpty() && sliding.peekFirst() == time) { // 먼저 벗어난다
                sliding.pollFirst()
            }
            val arrived = arrive[nextPerson] <= time
            val room = sliding.size < cap
            val gapPassed = lastStart == -1 || time - lastStart >= gap
            if (arrived && room && gapPassed) { // 그다음 맨 앞 사람 한 명이 출발한다
                sliding.addLast(time + ride)
                total += time - arrive[nextPerson]
                lastStart = time
                nextPerson++
            }
            time++
        }
        return total
    }
}
