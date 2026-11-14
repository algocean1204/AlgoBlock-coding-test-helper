class Solution {
    fun solution(solved: IntArray): Int {
        val ordered = solved.sortedDescending() // 많이 푼 회원부터
        var level = 0
        for (i in ordered.indices) {
            // 앞에서 i+1명은 모두 ordered[i]문제 이상 풀었다.
            // 그러니 ordered[i] >= i+1이면 'i+1문제 이상 푼 회원이 i+1명 이상'이 된다
            if (ordered[i] >= i + 1) {
                level = i + 1
            } else {
                break // 여기서 안 되면 더 큰 x도 안 된다
            }
        }
        return level
    }
}
