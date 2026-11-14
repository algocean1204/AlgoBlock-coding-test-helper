class Solution {
    fun solution(rows: Int, cols: Int, works: Array<IntArray>): Int {
        // 끝 다음 칸(r2 + 1행, c2 + 1열)에도 표시해야 하므로 한 행, 한 열씩 크게 만든다
        val diff = Array(rows + 1) { IntArray(cols + 1) }
        for (work in works) {
            val r1 = work[0]
            val c1 = work[1]
            val r2 = work[2]
            val c2 = work[3]
            val amount = work[4]
            diff[r1][c1] += amount
            diff[r1][c2 + 1] -= amount
            diff[r2 + 1][c1] -= amount
            diff[r2 + 1][c2 + 1] += amount
        }
        // 가로로 누적: 같은 행 안에서 왼쪽 표시를 오른쪽으로 펼친다
        for (r in 0..rows) {
            for (c in 1..cols) {
                diff[r][c] += diff[r][c - 1]
            }
        }
        // 세로로 누적: 같은 열 안에서 위쪽 표시를 아래로 펼친다
        for (r in 1..rows) {
            for (c in 0..cols) {
                diff[r][c] += diff[r - 1][c]
            }
        }
        // 값이 최대 3천만이라 Int로 충분하다
        var count = 0
        for (r in 0 until rows) {
            for (c in 0 until cols) {
                if (diff[r][c] == 0) {
                    count++
                }
            }
        }
        return count
    }
}
