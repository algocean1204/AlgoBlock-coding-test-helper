class Solution {
    fun solution(bracelets: Array<String>): Int {
        val count = HashMap<String, Int>()  // 대표 키 → 그 디자인의 팔찌 수
        var best = 0
        for (beads in bracelets) {
            val flipped = beads.reversed()  // 반대 방향으로 읽은 것
            var key = beads
            for (start in beads.indices) {
                // start번째 구슬부터 같은 방향으로, 그리고 뒤집어서 읽은 모습
                val same = beads.substring(start) + beads.substring(0, start)
                val other = flipped.substring(start) + flipped.substring(0, start)
                if (same < key) key = same
                if (other < key) key = other
            }
            // 사전 순으로 가장 앞선 모습을 대표로: 디자인이 같으면 키도 같다
            val now = (count[key] ?: 0) + 1
            count[key] = now
            best = maxOf(best, now)
        }
        return best
    }
}
