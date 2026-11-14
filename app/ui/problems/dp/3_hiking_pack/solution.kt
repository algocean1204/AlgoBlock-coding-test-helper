class Solution {
    fun solution(items: Array<IntArray>, capacity: Int): Int {
        val n = items.size
        // best[i][w]: 앞의 i개 물건만 보고, 무게 합이 w 이하가 되도록 골랐을 때 쓸모 점수 합의 최댓값
        val best = Array(n + 1) { IntArray(capacity + 1) }
        for (i in 1..n) {
            val weight = items[i - 1][0]
            val value = items[i - 1][1]
            for (w in 0..capacity) {
                best[i][w] = best[i - 1][w]  // i번째 물건을 넣지 않는다
                if (weight <= w) {  // i번째 물건을 넣는다: 나머지 무게 w - weight는 앞의 물건들로 채운다
                    best[i][w] = maxOf(best[i][w], best[i - 1][w - weight] + value)
                }
            }
        }
        return best[n][capacity]
    }
}
