class Solution {
    fun solution(n: Int, chargers: IntArray): Long {
        val fastest = chargers.min()
        // 시간은 최대 5 x 10^13이라 Int를 넘는다. 시간과 개수 합은 Long으로 둔다
        var left = 1L
        var right = fastest.toLong() * n
        while (left < right) {
            val mid = (left + right) / 2
            var done = 0L
            for (minute in chargers) {
                done += mid / minute
            }
            if (done >= n) {
                right = mid
            } else {
                left = mid + 1
            }
        }
        return left
    }
}
