class Solution {
    fun solution(gaps: IntArray, k: Int): Int {
        var count = 0
        var left = 0
        // gaps[left]부터 gaps[right]까지의 합 = left번 역에서 right + 1번 역까지의 거리
        // k가 10억까지라 합이 10억 + 1만 정도까지 가지만 Int(약 21억) 안이다
        var total = 0
        for (right in gaps.indices) {
            total += gaps[right]
            // 거리가 모두 양수라 왼쪽을 당기면 합이 줄어든다. k 이하가 될 때까지 당긴다
            while (total > k) {
                total -= gaps[left]
                left++
            }
            if (total == k) {
                count++
            }
        }
        return count
    }
}
