class Solution {
    fun solution(piles: IntArray): Int {
        val n = piles.size
        val prefix = IntArray(n + 1)  // prefix[i]: piles[0] ~ piles[i - 1]의 합
        for (i in 0 until n) {
            prefix[i + 1] = prefix[i] + piles[i]
        }
        val cost = Array(n) { IntArray(n) }  // cost[i][j]: i ~ j번째 더미를 한 더미로 만드는 최소 시간
        for (length in 2..n) {  // 짧은 구간부터 채운다
            for (i in 0..n - length) {
                val j = i + length - 1
                var best = Int.MAX_VALUE
                for (k in i until j) {  // 마지막에 [i, k] 더미와 [k + 1, j] 더미를 합친다
                    best = minOf(best, cost[i][k] + cost[k + 1][j])
                }
                cost[i][j] = best + prefix[j + 1] - prefix[i]  // 마지막 합치기에 드는 시간 = 구간 전체의 자루 수
            }
        }
        return cost[0][n - 1]
    }
}
