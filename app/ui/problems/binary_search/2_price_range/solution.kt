class Solution {
    // values에서 x 이상인 값이 처음 나오는 자리(없으면 길이)
    private fun firstAtLeast(values: IntArray, x: Int): Int {
        var left = 0
        var right = values.size
        while (left < right) {
            val mid = (left + right) / 2
            if (values[mid] >= x) {
                right = mid
            } else {
                left = mid + 1
            }
        }
        return left
    }

    fun solution(prices: IntArray, ranges: Array<IntArray>): IntArray {
        val sorted = prices.sortedArray()
        val answer = IntArray(ranges.size)
        for (i in ranges.indices) {
            val low = ranges[i][0]
            val high = ranges[i][1]
            val start = firstAtLeast(sorted, low)
            // 가격이 정수라서 'high보다 큰 값이 처음 나오는 자리' = 'high + 1 이상이 처음 나오는 자리'
            val end = firstAtLeast(sorted, high + 1)
            answer[i] = end - start
        }
        return answer
    }
}
