class Solution {
    // grid에서 (r, c)와 맞닿은 칸 가운데 mold인 칸의 수
    private fun count(grid: Array<CharArray>, r: Int, c: Int, mold: Char): Int {
        val dr = intArrayOf(-1, 1, 0, 0)
        val dc = intArrayOf(0, 0, -1, 1)
        var total = 0
        for (d in 0 until 4) {
            val nr = r + dr[d]
            val nc = c + dc[d]
            if (nr >= 0 && nr < grid.size && nc >= 0 && nc < grid[0].size && grid[nr][nc] == mold) total++
        }
        return total
    }

    fun solution(dish: Array<String>, hours: Int): Array<String> {
        val n = dish.size
        val m = dish[0].length
        var board = Array(n) { dish[it].toCharArray() }
        for (hour in 0 until hours) {
            // 1단계(번식): 1시간이 시작될 때의 board를 보고, 결과는 grown에 적는다
            val grown = Array(n) { board[it].clone() }
            for (r in 0 until n) {
                for (c in 0 until m) {
                    if (board[r][c] != '.') continue
                    val a = count(board, r, c, 'A')
                    val b = count(board, r, c, 'B')
                    if (a > b) grown[r][c] = 'A'
                    else if (b > a) grown[r][c] = 'B'
                    else if (a > 0) grown[r][c] = '#'
                }
            }
            // 2단계(포위): 1단계가 끝난 grown을 보고, 결과는 result에 적는다
            val result = Array(n) { grown[it].clone() }
            for (r in 0 until n) {
                for (c in 0 until m) {
                    if (grown[r][c] == 'A' && count(grown, r, c, 'B') >= 3) result[r][c] = '#'
                    else if (grown[r][c] == 'B' && count(grown, r, c, 'A') >= 3) result[r][c] = '#'
                }
            }
            var same = true // 1시간 동안 아무것도 바뀌지 않았으면 그 뒤로도 계속 같다
            for (r in 0 until n) {
                if (!result[r].contentEquals(board[r])) same = false
            }
            if (same) break
            board = result
        }
        return Array(n) { String(board[it]) }
    }
}
