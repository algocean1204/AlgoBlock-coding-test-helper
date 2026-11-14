import java.util.ArrayDeque

class Solution {
    fun solution(building: Array<String>): Int {
        val rows = building.size
        val cols = building[0].length
        val dr = intArrayOf(-1, 1, 0, 0)
        val dc = intArrayOf(0, 0, -1, 1)

        // 1. 불: 불이 난 칸을 모두 처음부터 큐에 넣고 한 번에 퍼뜨린다(여러 출발점 BFS)
        // fire[r][c]: 불이 (r, c)에 닿는 시각. -1은 불이 끝내 닿지 않는 칸
        val fire = Array(rows) { IntArray(cols) { -1 } }
        val queue = ArrayDeque<IntArray>()
        var startR = 0
        var startC = 0
        for (r in 0 until rows) {
            for (c in 0 until cols) {
                if (building[r][c] == 'F') {
                    fire[r][c] = 0
                    queue.add(intArrayOf(r, c))
                } else if (building[r][c] == 'S') {
                    startR = r
                    startC = c
                }
            }
        }
        while (queue.isNotEmpty()) {
            val cur = queue.poll()
            val r = cur[0]
            val c = cur[1]
            for (d in 0 until 4) {
                val nr = r + dr[d]
                val nc = c + dc[d]
                if (nr in 0 until rows && nc in 0 until cols && building[nr][nc] != '#' && fire[nr][nc] == -1) {
                    fire[nr][nc] = fire[r][c] + 1
                    queue.add(intArrayOf(nr, nc))
                }
            }
        }

        // 2. 사람: 불보다 먼저 닿는 칸으로만 움직이는 BFS
        val person = Array(rows) { IntArray(cols) { -1 } }
        person[startR][startC] = 0
        queue.add(intArrayOf(startR, startC))
        while (queue.isNotEmpty()) {
            val cur = queue.poll()
            val r = cur[0]
            val c = cur[1]
            for (d in 0 until 4) {
                val nr = r + dr[d]
                val nc = c + dc[d]
                if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue
                if (building[nr][nc] == '#' || person[nr][nc] != -1) continue
                val arrive = person[r][c] + 1
                if (fire[nr][nc] != -1 && fire[nr][nc] <= arrive) continue // 불이 같은 분이나 더 일찍 닿는 칸은 못 들어간다
                if (building[nr][nc] == 'E') return arrive
                person[nr][nc] = arrive
                queue.add(intArrayOf(nr, nc))
            }
        }
        return -1
    }
}
