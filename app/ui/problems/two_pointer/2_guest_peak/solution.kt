class Solution {
    fun solution(days: Int, bookings: Array<IntArray>): Int {
        // diff[d]: d일에 새로 늘어나는(음수면 줄어드는) 손님 수. last + 1일 = days + 1일까지 쓰므로 days + 2칸
        val diff = IntArray(days + 2)
        for (booking in bookings) {
            val first = booking[0]
            val last = booking[1]
            val guests = booking[2]
            diff[first] += guests
            diff[last + 1] -= guests
        }
        // 1일부터 누적하면 그날 묵는 사람 수가 된다 (최대 5천만이라 Int로 충분)
        var best = 0
        var staying = 0
        for (day in 1..days) {
            staying += diff[day]
            best = maxOf(best, staying)
        }
        return best
    }
}
