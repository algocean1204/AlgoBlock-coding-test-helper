import java.util.PriorityQueue

class Solution {
    fun solution(n: Int, rules: Array<IntArray>): IntArray {
        val after = Array(n + 1) { ArrayList<Int>() } // after[a]: a를 설치해야 설치할 수 있는 패키지들
        val waiting = IntArray(n + 1) // waiting[b]: b보다 먼저 설치해야 하는데 아직 설치하지 않은 패키지 수(진입 차수)
        for (r in rules) {
            after[r[0]].add(r[1])
            waiting[r[1]]++
        }

        val ready = PriorityQueue<Int>() // 기본 힙은 작은 것이 먼저 나온다
        for (p in 1..n) {
            if (waiting[p] == 0) ready.add(p)
        }
        val order = ArrayList<Int>()
        while (ready.isNotEmpty()) {
            val pkg = ready.poll()
            order.add(pkg)
            for (nxt in after[pkg]) {
                waiting[nxt]--
                if (waiting[nxt] == 0) ready.add(nxt)
            }
        }

        if (order.size < n) return intArrayOf() // 끝내 설치할 수 없는 패키지가 남았다: 규칙에 사이클이 있다
        return order.toIntArray()
    }
}
