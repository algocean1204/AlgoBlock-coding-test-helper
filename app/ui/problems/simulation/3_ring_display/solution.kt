class Solution {
    fun solution(board: Array<IntArray>, k: Int): Array<IntArray> {
        val n = board.size
        val m = board[0].size
        val result = Array(n) { board[it].clone() }
        for (ring in 0 until minOf(n, m) / 2) {
            val top = ring
            val bottom = n - 1 - ring
            val left = ring
            val right = m - 1 - ring
            // 고리의 칸을 왼쪽 위 모서리부터 시계 방향 순서로 늘어놓는다
            val cells = ArrayList<IntArray>()
            for (c in left..right) cells.add(intArrayOf(top, c))
            for (r in top + 1..bottom) cells.add(intArrayOf(r, right))
            for (c in right - 1 downTo left) cells.add(intArrayOf(bottom, c))
            for (r in bottom - 1 downTo top + 1) cells.add(intArrayOf(r, left))
            val length = cells.size
            var shift = k % length // 칸 수만큼 돌면 제자리로 돌아온다
            if (ring % 2 == 1) {
                shift = (length - shift) % length // 반시계 방향으로 shift칸 = 시계 방향으로 length - shift칸(음수의 나머지를 피한다)
            }
            // 시계 방향으로 shift칸 돌면 i번째 칸의 보석은 i + shift번째 칸으로 간다
            for (i in 0 until length) {
                val to = cells[(i + shift) % length]
                result[to[0]][to[1]] = board[cells[i][0]][cells[i][1]]
            }
        }
        return result
    }
}
