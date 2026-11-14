class Solution {
    fun solution(logs: Array<IntArray>, window: Int): IntArray {
        val answer = IntArray(logs.size)
        val candidates = ArrayDeque<IntArray>() // 아직 가장 큰 값이 될 수 있는 기록 [time, level]. 앞에서 뒤로 갈수록 level이 작다
        for ((k, log) in logs.withIndex()) {
            val time = log[0]
            val level = log[1]
            // 새 기록보다 작거나 같은 옛 기록은 다시는 가장 큰 값이 못 된다: 뒤에서 버린다
            while (candidates.isNotEmpty() && candidates.last()[1] <= level) {
                candidates.removeLast()
            }
            candidates.addLast(intArrayOf(time, level))
            // 창을 벗어난 오래된 기록은 앞에서 뺀다(여러 개일 수 있다). 방금 넣은 기록은 늘 창 안이라 덱이 비지 않는다
            while (candidates.first()[0] <= time - window) {
                candidates.removeFirst()
            }
            answer[k] = candidates.first()[1]
        }
        return answer
    }
}
