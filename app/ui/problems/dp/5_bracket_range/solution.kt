class Solution {
    fun solution(values: IntArray, signs: String): IntArray {
        val n = values.size
        val big = Array(n) { IntArray(n) }    // big[i][j]: values[i] ~ values[j]를 괄호로 묶어 만들 수 있는 가장 큰 값
        val small = Array(n) { IntArray(n) }  // small[i][j]: 같은 구간의 가장 작은 값
        for (i in 0 until n) {
            big[i][i] = values[i]
            small[i][i] = values[i]
        }
        for (length in 2..n) {  // 짧은 구간부터 채운다
            for (i in 0..n - length) {
                val j = i + length - 1
                var best = Int.MIN_VALUE
                var worst = Int.MAX_VALUE
                for (k in i until j) {  // signs[k]를 맨 마지막에 계산한다: [i, k]와 [k + 1, j]로 나뉜다
                    val high: Int
                    val low: Int
                    if (signs[k] == '+') {
                        high = big[i][k] + big[k + 1][j]
                        low = small[i][k] + small[k + 1][j]
                    } else if (signs[k] == '-') {
                        high = big[i][k] - small[k + 1][j]  // 빼는 쪽은 가장 작을 때 결과가 가장 크다
                        low = small[i][k] - big[k + 1][j]
                    } else {  // '^': 두 값 가운데 큰 값
                        high = maxOf(big[i][k], big[k + 1][j])
                        low = maxOf(small[i][k], small[k + 1][j])  // 큰 값을 작게 하려면 양쪽을 모두 작게 한다
                    }
                    best = maxOf(best, high)
                    worst = minOf(worst, low)
                }
                big[i][j] = best
                small[i][j] = worst
            }
        }
        return intArrayOf(big[0][n - 1], small[0][n - 1])
    }
}
