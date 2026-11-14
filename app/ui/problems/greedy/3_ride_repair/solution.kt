class Solution {
    fun solution(fix: IntArray, line: IntArray, walk: Int): Long {
        // a 다음에 b를 고치면 b의 손님이 (fix[a] + walk) × line[b]만큼 더 기다리고,
        // b 다음에 a를 고치면 a의 손님이 (fix[b] + walk) × line[a]만큼 더 기다린다 → 작은 쪽 차례가 앞
        val order = fix.indices.sortedWith(Comparator { a, b ->
            ((fix[a] + walk).toLong() * line[b]).compareTo((fix[b] + walk).toLong() * line[a])
        })

        var now = 0L  // 지금 시각
        var total = 0L  // 기다림의 합 (Int를 넘을 수 있다)
        for ((k, ride) in order.withIndex()) {
            if (k > 0) {
                now += walk  // 다음 놀이기구까지 걸어간다(첫 놀이기구는 걷지 않는다)
            }
            now += fix[ride]  // 이 놀이기구를 다 고친 시각
            total += now * line[ride]
        }
        return total
    }
}
