class Solution {
    fun solution(road: String, t: Long): Long {
        val n = road.length
        val firstSeen = HashMap<String, Int>() // 도로 모습 → 그 모습이 처음 나온 시각(초)
        val passed = ArrayList<Long>()          // passed[s] = 처음 s초 동안 결승선을 지나간 횟수
        passed.add(0L)
        var state = road
        var second = 0
        while (second < t && !firstSeen.containsKey(state)) {
            firstSeen[state] = second
            val crossed = if (state[n - 1] == '>' && state[0] == '.') 1L else 0L
            // 1초가 시작될 때의 state만 보고 새 도로 newRoad에 적는다
            val newRoad = CharArray(n) { '.' }
            for (i in 0 until n) {
                if (state[i] == '>') {
                    val front = (i + 1) % n
                    if (state[front] == '.') newRoad[front] = '>'
                    else newRoad[i] = '>'
                }
            }
            state = String(newRoad)
            second++
            passed.add(passed[passed.size - 1] + crossed)
        }
        if (second.toLong() == t) return passed[t.toInt()]
        // second초의 모습이 start초에 이미 나왔다: start초부터 cycle초마다 같은 흐름이 되풀이된다
        val start = firstSeen[state]!!
        val cycle = second - start
        val perCycle = passed[second] - passed[start]
        val full = (t - start) / cycle // t가 Int를 넘으므로 Long으로 계산한다
        val rest = ((t - start) % cycle).toInt()
        return passed[start] + full * perCycle + (passed[start + rest] - passed[start])
    }
}
