import java.util.ArrayDeque

class Solution {
    fun solution(n: Int, cables: Array<IntArray>, start: Int, offline: IntArray): IntArray {
        val neighbors = Array(n + 1) { ArrayList<Int>() }
        for (cable in cables) {
            neighbors[cable[0]].add(cable[1]) // 케이블은 양쪽 방향이다
            neighbors[cable[1]].add(cable[0])
        }
        val off = BooleanArray(n + 1) // off[v]: v번 서버가 꺼져 있는가
        for (server in offline) off[server] = true

        // minute[v]: v번 서버가 파일을 받는 시각. -1은 아직(또는 끝내) 받지 못한 서버
        val minute = IntArray(n + 1) { -1 }
        minute[start] = 0
        val queue = ArrayDeque<Int>()
        queue.add(start)
        while (queue.isNotEmpty()) {
            val server = queue.poll()
            for (next in neighbors[server]) {
                if (minute[next] == -1 && !off[next]) { // 꺼진 서버는 받지도 보내지도 않는다
                    minute[next] = minute[server] + 1
                    queue.add(next)
                }
            }
        }
        val latest = minute.max() // start번 서버가 0분이라 받지 못한 서버(-1)는 가장 큰 값이 되지 않는다
        return intArrayOf(latest, minute.count { it == latest })
    }
}
