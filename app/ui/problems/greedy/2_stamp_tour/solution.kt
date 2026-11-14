class Solution {
    fun solution(kinds: Array<String>, minutes: IntArray, time: Int): Int {
        // 모양마다 그 도장을 받는 가장 짧은 시간만 남긴다(같은 모양은 한 칸만 채우므로)
        val shortest = HashMap<String, Int>()
        for (i in kinds.indices) {
            val before = shortest[kinds[i]]
            if (before == null || minutes[i] < before) {
                shortest[kinds[i]] = minutes[i]
            }
        }
        val sorted = shortest.values.sorted()  // 짧은 것부터

        var used = 0L  // 지금까지 쓴 시간
        var filled = 0  // 채운 칸 수
        for (minute in sorted) {
            if (used + minute > time) {
                break  // 이것이 안 들어가면 뒤의 더 긴 것도 안 들어간다
            }
            used += minute
            filled++
        }
        return filled
    }
}
