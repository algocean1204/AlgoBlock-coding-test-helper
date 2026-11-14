import java.util.PriorityQueue

class Solution {
    private val INF = Long.MAX_VALUE / 4  // 시간 합이 Int를 넘으므로 Long, 더해도 넘치지 않게 넉넉히

    private fun dijkstra(graph: Array<ArrayList<LongArray>>, n: Int, start: Int): LongArray {
        val dist = LongArray(n + 1) { INF }
        dist[start] = 0
        val heap = PriorityQueue<LongArray>(compareBy { it[0] })
        heap.add(longArrayOf(0, start.toLong()))
        while (heap.isNotEmpty()) {
            val (d, nowLong) = heap.poll()
            val now = nowLong.toInt()
            if (d > dist[now]) {
                continue
            }
            for (edge in graph[now]) {
                val nxt = edge[0].toInt()
                if (d + edge[1] < dist[nxt]) {
                    dist[nxt] = d + edge[1]
                    heap.add(longArrayOf(dist[nxt], nxt.toLong()))
                }
            }
        }
        return dist
    }

    fun solution(n: Int, roads: Array<IntArray>, farms: IntArray, market: Int): Long {
        val small = Array(n + 1) { ArrayList<LongArray>() }  // 작은 트럭: u → v, slow분
        val bigBack = Array(n + 1) { ArrayList<LongArray>() }  // 큰 트럭의 도로를 거꾸로 뒤집은 것: v → u, fast분
        for (r in roads) {
            small[r[0]].add(longArrayOf(r[1].toLong(), r[2].toLong()))
            bigBack[r[1]].add(longArrayOf(r[0].toLong(), r[3].toLong()))
        }

        // 뒤집은 그래프에서 시장으로부터의 거리 = 각 마을에서 시장까지 큰 트럭이 걸리는 시간
        val toMarket = dijkstra(bigBack, n, market)

        val gather = LongArray(n + 1)  // gather[m]: 작은 트럭이 모두 m번 마을에 모이는 시각(가장 늦게 도착한 트럭)
        for (farm in farms) {
            val arrive = dijkstra(small, n, farm)
            for (m in 1..n) {
                gather[m] = maxOf(gather[m], arrive[m])
            }
        }

        var answer = INF
        for (m in 1..n) {  // 모이는 마을을 모두 해 본다. 닿지 못하는 곳은 무한대라 뽑히지 않는다
            if (gather[m] < INF && toMarket[m] < INF) {
                answer = minOf(answer, gather[m] + toMarket[m])
            }
        }
        return if (answer < INF) answer else -1
    }
}
