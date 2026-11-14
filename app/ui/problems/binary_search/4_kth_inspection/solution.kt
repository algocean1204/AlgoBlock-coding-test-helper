class Solution {
    // day일까지(그날 포함) 이루어진 점검 수. 모두 400억 번까지라 Long으로 센다
    private fun countUntil(schedules: Array<IntArray>, day: Long): Long {
        var total = 0L
        for (s in schedules) {
            val first = s[0].toLong()
            val gap = s[1].toLong()
            val times = s[2].toLong()
            if (day >= first) {  // 첫 점검 전이면 0번
                total += minOf(times, (day - first) / gap + 1)  // times번을 넘지 않는다
            }
        }
        return total
    }

    fun solution(schedules: Array<IntArray>, k: Long): Long {
        var left = Long.MAX_VALUE
        var right = 0L
        for (s in schedules) {
            left = minOf(left, s[0].toLong())
            right = maxOf(right, s[0] + (s[2] - 1).toLong() * s[1])
        }
        // 그날까지의 점검이 k번 이상인 가장 이른 날을 찾는다
        while (left < right) {
            val mid = (left + right) / 2
            if (countUntil(schedules, mid) >= k) {
                right = mid
            } else {
                left = mid + 1
            }
        }
        return left
    }
}
