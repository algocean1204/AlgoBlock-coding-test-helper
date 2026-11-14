import java.util.PriorityQueue

class Solution {
    fun solution(n: Int, roads: Array<IntArray>, k: Int): Int {
        val graph = Array(n + 1) { ArrayList<IntArray>() }
        for (road in roads) {
            graph[road[0]].add(intArrayOf(road[1], road[2]))
            graph[road[1]].add(intArrayOf(road[0], road[2]))
        }

        // dist[city][used][just]: 통행권을 used장 쓰고 city에 왔을 때 낸 통행료 합의 최솟값(최대 약 1억6천만이라 Int로 충분)
        // just는 바로 앞 도로에 통행권을 썼으면 1, 통행료를 냈으면(또는 아직 출발 전이면) 0
        val dist = Array(n + 1) { Array(k + 1) { IntArray(2) { Int.MAX_VALUE } } }
        dist[1][0][0] = 0
        // 힙에는 [통행료 합, 도시, 쓴 통행권 수, 바로 앞에 썼는가]를 넣고 통행료(첫 칸)가 작은 것부터 꺼낸다
        val heap = PriorityQueue<IntArray>(compareBy { it[0] })
        heap.add(intArrayOf(0, 1, 0, 0))
        while (heap.isNotEmpty()) {
            val top = heap.poll()
            val cost = top[0]
            val city = top[1]
            val used = top[2]
            val just = top[3]
            if (cost > dist[city][used][just]) continue
            if (city == n) return cost  // 몇 장을 썼든 n번 도시를 처음 꺼낸 값이 가장 싸다(통행권은 남겨도 된다)
            for (edge in graph[city]) {
                val nxt = edge[0]
                val toll = edge[1]
                if (cost + toll < dist[nxt][used][0]) {  // 통행료를 낸다
                    dist[nxt][used][0] = cost + toll
                    heap.add(intArrayOf(cost + toll, nxt, used, 0))
                }
                if (used < k && just == 0 && cost < dist[nxt][used + 1][1]) {  // 통행권을 쓴다(바로 앞 도로에 쓰지 않았을 때만)
                    dist[nxt][used + 1][1] = cost
                    heap.add(intArrayOf(cost, nxt, used + 1, 1))
                }
            }
        }
        return -1
    }
}
