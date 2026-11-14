class Solution {
    fun solution(presses: IntArray, m: Int): Long {
        // 조명 상태를 정수 하나로 담는다: k번 조명이 켜져 있으면 (k - 1)번째 비트가 1
        val seen = HashMap<Int, Int>()  // 상태 → 지금까지 그 상태가 나온 횟수
        seen[0] = 1  // 아무것도 누르지 않은 처음(모두 꺼짐)도 한 번
        var state = 0
        var total = 0L  // 토막 수는 Int를 넘을 수 있다
        for (button in presses) {
            if (button == 0) {
                state = 0  // 모두 끈다
            } else {
                state = state xor (1 shl (button - 1))  // 그 조명만 뒤집는다
            }
            // 앞서 지금과 같은 상태였던 때마다, 그 다음 버튼부터 지금 버튼까지가 제자리 토막이다
            val before = seen[state] ?: 0
            total += before
            seen[state] = before + 1
        }
        return total
    }
}
