class Solution {
    fun solution(profits: IntArray, target: Int): Long {
        // seen[s]: 지금까지 나온 누적 합 가운데 값이 s인 것의 개수
        // 아무 날도 더하지 않은 누적 합 0을 한 번 넣어 두어야 첫째 날부터 시작하는 기간도 센다
        val seen = HashMap<Long, Int>()
        seen[0L] = 1
        var total = 0L
        // 개수가 최대 약 50억이라 Int가 넘친다. Long을 쓴다
        var count = 0L
        for (profit in profits) {
            total += profit
            // 앞쪽 누적 합이 total - target이었다면, 그다음 날부터 오늘까지의 합이 target이다
            // getOrDefault: 키가 없으면 0을 돌려준다
            count += seen.getOrDefault(total - target, 0)
            seen[total] = seen.getOrDefault(total, 0) + 1
        }
        return count
    }
}
