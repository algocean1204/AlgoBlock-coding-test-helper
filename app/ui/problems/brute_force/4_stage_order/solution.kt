class Solution {
    // remaining: 더 놓아야 할 자리 수, last: 바로 앞에 놓은 장르 번호(처음에는 -1)
    private fun place(remaining: Int, last: Int, left: IntArray): Long {
        if (remaining == 0) {
            return 1L
        }
        var ways = 0L // 경우의 수가 Int를 넘을 수 있어 Long으로 센다
        for (genre in left.indices) {
            if (left[genre] == 0 || genre == last) { // 놓는 도중에 가지를 끊는다
                continue
            }
            left[genre]--
            ways += place(remaining - 1, genre, left)
            left[genre]++
        }
        return ways
    }

    fun solution(genres: Array<String>): Int {
        // 같은 장르를 개수로 묶는다: left[장르 번호] = 아직 안 놓은 팀 수
        val number = HashMap<String, Int>()
        for (genre in genres) {
            if (!number.containsKey(genre)) {
                number[genre] = number.size
            }
        }
        val left = IntArray(number.size)
        for (genre in genres) {
            left[number[genre]!!]++
        }
        return place(genres.size, -1, left).toInt()
    }
}
