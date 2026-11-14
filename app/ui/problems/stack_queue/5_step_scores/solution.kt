class Solution {
    fun solution(scores: IntArray, jump: Int): Long {
        val n = scores.size
        val best = LongArray(n) // best[i]: i번 돌에 섰을 때까지 모은 점수의 가장 큰 값. 합이 Int를 넘을 수 있어 Long
        best[0] = scores[0].toLong()
        val window = ArrayDeque<Int>() // 바로 앞 jump개 돌의 번호. 앞에서 뒤로 갈수록 best가 작다
        window.addLast(0)
        for (i in 1 until n) {
            // i번 돌로 한 번에 올 수 없는 돌(jump칸보다 먼 돌)은 앞에서 뺀다
            while (window.first() < i - jump) {
                window.removeFirst()
            }
            best[i] = scores[i] + best[window.first()]
            // best[i]보다 작거나 같은 돌은 앞으로 고를 일이 없다: 뒤에서 버린다
            while (window.isNotEmpty() && best[window.last()] <= best[i]) {
                window.removeLast()
            }
            window.addLast(i)
        }
        return best[n - 1]
    }
}
