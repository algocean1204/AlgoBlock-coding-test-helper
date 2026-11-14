import java.util.PriorityQueue
import kotlin.math.abs
import kotlin.math.max

class Solution {
    fun solution(ground: Array<IntArray>): Int {
        val rows = ground.size
        val cols = ground[0].size
        // 그 칸까지 가는 길에서 넘는 가장 높은 턱의 최솟값
        val highest = Array(rows) { IntArray(cols) { Int.MAX_VALUE } }
        highest[0][0] = 0
        // 힙에는 [턱 높이, 행, 열]을 넣고 턱(첫 칸)이 낮은 것부터 꺼낸다
        val heap = PriorityQueue<IntArray>(compareBy { it[0] })
        heap.add(intArrayOf(0, 0, 0))
        val dr = intArrayOf(-1, 1, 0, 0)
        val dc = intArrayOf(0, 0, -1, 1)
        while (heap.isNotEmpty()) {
            val top = heap.poll()
            val h = top[0]
            val r = top[1]
            val c = top[2]
            if (h > highest[r][c]) continue
            if (r == rows - 1 && c == cols - 1) return h
            for (k in 0 until 4) {
                val nr = r + dr[k]
                val nc = c + dc[k]
                if (nr in 0 until rows && nc in 0 until cols) {
                    val ledge = abs(ground[nr][nc] - ground[r][c])
                    val cur = max(h, ledge)  // 합이 아니라 가장 높은 턱
                    if (cur < highest[nr][nc]) {
                        highest[nr][nc] = cur
                        heap.add(intArrayOf(cur, nr, nc))
                    }
                }
            }
        }
        return highest[rows - 1][cols - 1]
    }
}
