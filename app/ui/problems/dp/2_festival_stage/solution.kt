class Solution {
    fun solution(pay: IntArray): Int {
        val n = pay.size
        if (n == 1) {
            return pay[0]
        }
        // 길이가 10만이라 재귀 대신 반복문으로 앞에서부터 채운다
        val best = IntArray(n)  // best[i]: 0 ~ i번째 날만 보고 골랐을 때 사례금 합의 최댓값
        best[0] = pay[0]
        best[1] = maxOf(pay[0], pay[1])
        for (i in 2 until n) {
            val rest = best[i - 1]  // i번째 날은 쉰다
            val perform = best[i - 2] + pay[i]  // i번째 날 공연한다: 바로 앞날은 쉬었어야 한다
            best[i] = maxOf(rest, perform)
        }
        return best[n - 1]
    }
}
