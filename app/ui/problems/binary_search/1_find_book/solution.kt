class Solution {
    fun solution(books: IntArray, queries: IntArray): IntArray {
        val answer = IntArray(queries.size)
        for (i in queries.indices) {
            val target = queries[i]
            var left = 0
            var right = books.size - 1
            var position = -1
            while (left <= right) {
                val mid = (left + right) / 2
                if (books[mid] == target) {
                    position = mid
                    break
                } else if (books[mid] < target) {
                    left = mid + 1
                } else {
                    right = mid - 1
                }
            }
            answer[i] = position
        }
        return answer
    }
}
