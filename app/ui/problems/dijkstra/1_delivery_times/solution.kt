import java.util.PriorityQueue

class Solution {
    fun solution(n: Int, roads: Array<IntArray>): IntArray {
        val graph = Array(n + 1) { ArrayList<IntArray>() }
        for (road in roads) {
            graph[road[0]].add(intArrayOf(road[1], road[2]))
            graph[road[1]].add(intArrayOf(road[0], road[2]))
        }

        val INF = Int.MAX_VALUE  // 최대 시간은 약 6억이라 Int로 충분하다
        val dist = IntArray(n + 1) { INF }
        dist[1] = 0
        // 힙에는 [시간, 마을]을 넣고, 시간(첫 칸)이 작은 것부터 꺼내도록 비교 기준을 준다
        val heap = PriorityQueue<IntArray>(compareBy { it[0] })
        heap.add(intArrayOf(0, 1))
        while (heap.isNotEmpty()) {
            val top = heap.poll()
            val d = top[0]
            val now = top[1]
            if (d > dist[now]) continue  // 이미 더 짧은 시간으로 확정된 마을
            for (edge in graph[now]) {
                val nxt = edge[0]
                val time = edge[1]
                if (d + time < dist[nxt]) {
                    dist[nxt] = d + time
                    heap.add(intArrayOf(dist[nxt], nxt))
                }
            }
        }
        return dist.copyOfRange(1, n + 1)
    }
}
