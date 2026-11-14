class Solution {
    fun solution(n: Int): Long {
        // 탑의 수는 Int 범위를 넘으므로 Long으로 담는다
        val ways = LongArray(n + 1)  // ways[h]: 높이가 정확히 h인 탑의 수
        ways[0] = 1L  // 아무것도 쌓지 않은 높이 0의 탑 하나
        for (height in 1..n) {
            for (block in 1..3) {  // 맨 위에 놓은 블록의 높이
                if (height - block >= 0) {
                    ways[height] += ways[height - block]
                }
            }
        }
        return ways[n]
    }
}
