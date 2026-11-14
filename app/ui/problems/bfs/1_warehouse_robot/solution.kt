import java.util.ArrayDeque

class Solution {
    fun solution(floor: Array<String>): Int {
        val rows = floor.size
        val cols = floor[0].length
        var startR = 0
        var startC = 0
        for (r in 0 until rows) {
            for (c in 0 until cols) {
                if (floor[r][c] == 'S') { startR = r; startC = c }
            }
        }
        // distance[r][c]: 출발 칸에서 (r, c)까지의 이동 횟수. -1은 아직 가 보지 않은 칸
        val distance = Array(rows) { IntArray(cols) { -1 } }
        distance[startR][startC] = 0
        val queue = ArrayDeque<IntArray>()
        queue.add(intArrayOf(startR, startC))
        val dr = intArrayOf(-1, 1, 0, 0)
        val dc = intArrayOf(0, 0, -1, 1)
        while (queue.isNotEmpty()) {
            val cur = queue.poll()
            val r = cur[0]
            val c = cur[1]
            if (floor[r][c] == 'E') return distance[r][c]
            for (d in 0 until 4) {
                val nr = r + dr[d]
                val nc = c + dc[d]
                if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue
                if (floor[nr][nc] == '#' || distance[nr][nc] != -1) continue
                distance[nr][nc] = distance[r][c] + 1 // 넣을 때 바로 적어야 같은 칸이 두 번 들어가지 않는다
                queue.add(intArrayOf(nr, nc))
            }
        }
        return -1
    }
}
