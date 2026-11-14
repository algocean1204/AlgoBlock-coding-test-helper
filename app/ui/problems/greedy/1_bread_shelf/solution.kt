class Solution {
    fun solution(baked: IntArray, want: IntArray, fresh: Int): Int {
        val n = baked.size
        val left = baked.copyOf() // left[d]: d일에 구운 빵 가운데 아직 남은 개수
        var oldest = 0            // 아직 남은 빵이 있을 수 있는 가장 오래된 날
        var sold = 0
        for (day in 0 until n) {
            oldest = maxOf(oldest, day - fresh + 1) // 기한이 지난 날의 빵은 버린다
            var need = want[day]
            while (need > 0 && oldest <= day) { // 가장 오래된 빵부터 판다
                val take = minOf(need, left[oldest])
                left[oldest] -= take
                need -= take
                sold += take
                if (left[oldest] == 0) {
                    oldest++ // 다 팔린 날은 다시 보지 않는다
                }
            }
        }
        return sold
    }
}
