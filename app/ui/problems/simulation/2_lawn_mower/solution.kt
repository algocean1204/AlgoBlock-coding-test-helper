class Solution {
    fun solution(garden: Array<String>, commands: String): Int {
        val rows = garden.size
        val cols = garden[0].length
        // 위, 오른쪽, 아래, 왼쪽: 시계 방향 순서. 오른쪽으로 돌면 +1, 왼쪽으로 돌면 -1
        val dr = intArrayOf(-1, 0, 1, 0)
        val dc = intArrayOf(0, 1, 0, -1)
        var row = 0
        var col = 0
        for (r in 0 until rows) {
            for (c in 0 until cols) {
                if (garden[r][c] == 'S') {
                    row = r
                    col = c
                }
            }
        }
        var direction = 0
        val mowed = Array(rows) { BooleanArray(cols) }
        mowed[row][col] = true
        var count = 1
        for (command in commands) {
            if (command == 'L') {
                direction = (direction + 3) % 4 // 왼쪽으로 한 번 = 오른쪽으로 세 번(음수의 나머지가 음수가 되는 것을 피한다)
            } else if (command == 'R') {
                direction = (direction + 1) % 4
            } else {
                val nextRow = row + dr[direction]
                val nextCol = col + dc[direction]
                if (nextRow in 0 until rows && nextCol in 0 until cols && garden[nextRow][nextCol] != '#') {
                    row = nextRow
                    col = nextCol
                    if (!mowed[row][col]) {
                        mowed[row][col] = true
                        count++
                    }
                }
            }
        }
        return count
    }
}
