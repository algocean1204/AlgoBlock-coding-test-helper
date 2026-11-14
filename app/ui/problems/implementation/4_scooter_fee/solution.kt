class Solution {
    // 할증 시간: 07:30 이상 09:30 미만, 17:00 이상 19:00 미만(분)
    private val rush = listOf(Pair(7 * 60 + 30, 9 * 60 + 30), Pair(17 * 60, 19 * 60))

    private fun toMinutes(clock: String): Int = clock.substring(0, 2).toInt() * 60 + clock.substring(3).toInt()

    private fun rideFee(start: Int, end: Int, perMinute: Int): Int {
        // 탄 분마다 1분 요금, 할증 시간과 겹친 분은 1분 요금을 한 번 더
        var fee = (end - start) * perMinute
        for ((rushStart, rushEnd) in rush) {
            val overlap = minOf(end, rushEnd) - maxOf(start, rushStart)
            if (overlap > 0) {
                fee += overlap * perMinute
            }
        }
        return fee
    }

    fun solution(rides: Array<String>, price: IntArray, gap: Int): Array<IntArray> {
        val unlock = price[0]
        val perMinute = price[1]
        val dayMax = price[2]

        val total = HashMap<String, Int>()  // 회원 → 그날 요금 합
        val lastEnd = HashMap<String, Int>()  // 회원 → 바로 앞 기록의 끝 시각(분)
        for (ride in rides) {
            val words = ride.split(" ")
            val member = words[0]
            val start = toMinutes(words[1])
            val end = toMinutes(words[2])
            var fee = rideFee(start, end, perMinute)
            // 같은 회원의 바로 앞 기록이 끝난 지 gap분 이하이면 이어 탄 것: 잠금 해제 요금이 없다
            val previous = lastEnd[member]
            if (previous == null || start - previous > gap) {
                fee += unlock
            }
            total[member] = (total[member] ?: 0) + fee
            lastEnd[member] = end
        }

        val answer = ArrayList<IntArray>()
        for ((member, sum) in total) {
            answer.add(intArrayOf(member.toInt(), minOf(sum, dayMax)))  // 상한은 하루 합에 한 번
        }
        // 요금이 많은 회원부터, 같으면 번호가 작은 회원부터
        answer.sortWith(compareBy<IntArray>({ -it[1] }, { it[0] }))
        return answer.toTypedArray()
    }
}
