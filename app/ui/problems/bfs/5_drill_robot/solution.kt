import java.util.ArrayDeque

class Solution {
    fun solution(mine: Array<IntArray>, drill: Int): Int {
        val rows = mine.size
        val cols = mine[0].size
        val dr = intArrayOf(-1, 1, 0, 0)
        val dc = intArrayOf(0, 0, -1, 1)

        // 상태 = (행, 열, 지금까지 쓴 드릴 수). 같은 칸이라도 쓴 드릴 수가 다르면 다른 상태다
        // distance[r][c][used]: 그 상태까지의 최소 이동 횟수. -1은 아직 가 보지 않은 상태
        val distance = Array(rows) { Array(cols) { IntArray(drill + 1) { -1 } } }
        distance[0][0][0] = 0
        val queue = ArrayDeque<IntArray>()
        queue.add(intArrayOf(0, 0, 0))
        while (queue.isNotEmpty()) {
            val cur = queue.poll()
            val r = cur[0]
            val c = cur[1]
            val used = cur[2]
            if (r == rows - 1 && c == cols - 1) return distance[r][c][used]
            for (d in 0 until 4) {
                val nr = r + dr[d]
                val nc = c + dc[d]
                if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue
                val nextUsed = used + mine[nr][nc] // 바위 칸이면 드릴을 한 번 더 쓴다
                if (nextUsed > drill) continue
                if (distance[nr][nc][nextUsed] != -1) continue
                distance[nr][nc][nextUsed] = distance[r][c][used] + 1
                queue.add(intArrayOf(nr, nc, nextUsed))
            }
        }
        return -1
    }
}
