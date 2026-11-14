class Solution {
    fun solution(n: Int, tracks: Array<IntArray>, queries: Array<IntArray>): IntArray {
        val INF = 1_000_000_000L // 가장 긴 최단 시간(299,000)보다 크고, 두 번 더해도 넘치지 않게 Long으로 둔다
        val dist = Array(n + 1) { LongArray(n + 1) { INF } }
        for (s in 1..n) dist[s][s] = 0
        for (t in tracks) {
            if (t[2] < dist[t[0]][t[1]]) { // 같은 두 역 사이 선로가 여럿이면 짧은 것만 남긴다
                dist[t[0]][t[1]] = t[2].toLong()
                dist[t[1]][t[0]] = t[2].toLong()
            }
        }

        val asked = Array(n + 1) { ArrayList<Int>() } // asked[k]: k번 역까지 열렸을 때를 묻는 질문의 번호들
        for ((i, q) in queries.withIndex()) asked[q[0]].add(i)

        val answer = IntArray(queries.size)
        for (k in 1..n) {
            // 플로이드: k번 역을 거쳐 가는 길로 모든 두 역 사이 거리를 고친다(아직 닫힌 역까지의 거리도 고쳐 둔다)
            for (i in 1..n) {
                for (j in 1..n) {
                    if (dist[i][k] + dist[k][j] < dist[i][j]) {
                        dist[i][j] = dist[i][k] + dist[k][j]
                    }
                }
            }
            // 이제 dist[a][b]는 1~k번 역만 거쳐 가는 가장 짧은 시간이다
            for (idx in asked[k]) {
                val d = dist[queries[idx][1]][queries[idx][2]]
                answer[idx] = if (d >= INF) -1 else d.toInt()
            }
        }
        return answer
    }
}
