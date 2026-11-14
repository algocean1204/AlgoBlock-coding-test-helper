import java.util.PriorityQueue

class Solution {
    fun solution(routes: Array<String>, start: String, goal: String): Int {
        // 선착장 이름마다 0부터 번호를 매기고, 번호로 인접 목록을 만든다
        val id = HashMap<String, Int>()
        val graph = ArrayList<ArrayList<IntArray>>()
        fun getId(name: String): Int {
            if (!id.containsKey(name)) {
                id[name] = id.size
                graph.add(ArrayList())
            }
            return id[name]!!
        }
        for (route in routes) {
            val part = route.split(" ")
            val from = getId(part[0])
            val to = getId(part[1])
            graph[from].add(intArrayOf(to, part[2].toInt()))
        }

        val source = id[start]!!
        val target = id[goal]!!
        val dist = IntArray(id.size) { Int.MAX_VALUE }  // 최대 시간은 6천만 정도라 Int로 충분하다
        dist[source] = 0
        // 힙에는 [시간, 선착장 번호]를 넣고 시간(첫 칸)이 작은 것부터 꺼낸다
        val heap = PriorityQueue<IntArray>(compareBy { it[0] })
        heap.add(intArrayOf(0, source))
        while (heap.isNotEmpty()) {
            val top = heap.poll()
            val d = top[0]
            val now = top[1]
            if (d > dist[now]) continue  // 이미 더 빠른 시간으로 확정된 선착장
            if (now == target) return d  // 도착점은 큐에서 꺼낼 때 확정된다
            for (edge in graph[now]) {
                val nxt = edge[0]
                val minutes = edge[1]
                if (d + minutes < dist[nxt]) {
                    dist[nxt] = d + minutes
                    heap.add(intArrayOf(dist[nxt], nxt))
                }
            }
        }
        return -1
    }
}
