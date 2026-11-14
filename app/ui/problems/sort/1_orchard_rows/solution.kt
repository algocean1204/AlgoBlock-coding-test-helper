class Solution {
    fun solution(rows: Int, apples: Array<IntArray>, k: Int): IntArray {
        val kindsOf = Array(rows + 1) { HashSet<Int>() }  // kindsOf[줄 번호] = 그 줄의 서로 다른 무게(0번 칸은 쓰지 않는다)
        for (apple in apples) {
            kindsOf[apple[0]].add(apple[1])  // 같은 무게는 한 번만
        }

        val answer = IntArray(rows)
        for (row in 1..rows) {
            val kinds = kindsOf[row].sortedDescending()  // 무거운 것부터
            // k번째 무게는 위치 k-1. 적은 무게가 k개보다 적으면 -1(사과가 없는 줄 포함)
            answer[row - 1] = if (k <= kinds.size) kinds[k - 1] else -1
        }
        return answer
    }
}
