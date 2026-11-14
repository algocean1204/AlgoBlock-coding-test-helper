class Solution {
    fun solution(rows: Int, cols: Int, start: IntArray, commands: String): IntArray {
        var row = start[0]
        var col = start[1]
        for (command in commands) {
            var dr = 0
            var dc = 0
            when (command) {
                'N' -> dr = -1
                'S' -> dr = 1
                'W' -> dc = -1
                else -> dc = 1
            }
            val nextRow = row + dr
            val nextCol = col + dc
            if (nextRow in 0 until rows && nextCol in 0 until cols) {
                row = nextRow
                col = nextCol
            }
        }
        return intArrayOf(row, col)
    }
}
