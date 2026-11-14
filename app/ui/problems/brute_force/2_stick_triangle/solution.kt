class Solution {
    fun solution(sticks: IntArray): Int {
        var count = 0
        val n = sticks.size
        for (i in 0 until n) {
            for (j in i + 1 until n) {
                for (k in j + 1 until n) {
                    // 세 막대 중 가장 긴 것과 나머지 둘의 합을 비교한다. 합은 Long으로 계산해 넘침을 막는다
                    val a = sticks[i].toLong()
                    val b = sticks[j].toLong()
                    val c = sticks[k].toLong()
                    val longest = maxOf(a, maxOf(b, c))
                    val sum = a + b + c - longest // 가장 긴 것을 뺀 두 막대의 합
                    if (longest < sum) {
                        count++
                    }
                }
            }
        }
        return count
    }
}
