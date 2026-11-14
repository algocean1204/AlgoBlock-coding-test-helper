class Solution {
    fun solution(visitors: IntArray, queries: Array<IntArray>): IntArray {
        // prefix[i]: 1일부터 i일까지 방문자 수의 합. prefix[0]은 아무 날도 더하지 않은 0
        // 합은 최대 10만 × 1만 = 10억이라 Int에 들어간다
        val prefix = IntArray(visitors.size + 1)
        for (i in visitors.indices) {
            prefix[i + 1] = prefix[i] + visitors[i]
        }
        val answer = IntArray(queries.size)
        for (q in queries.indices) {
            val start = queries[q][0]
            val end = queries[q][1]
            answer[q] = prefix[end] - prefix[start - 1]
        }
        return answer
    }
}
