class Solution {
    fun solution(floor: Array<String>): Int {
        val rows = floor.size
        val cols = floor[0].length
        val visited = Array(rows) { BooleanArray(cols) }
        val dr = intArrayOf(-1, 1, 0, 0)
        val dc = intArrayOf(0, 0, -1, 1)
        var count = 0
        for (r in 0 until rows) {
            for (c in 0 until cols) {
                if (floor[r][c] != '#' || visited[r][c]) continue
                // 아직 어느 웅덩이에도 들지 않은 물 칸: 새 웅덩이를 하나 세고, 이어진 칸을 모두 방문 표시한다
                count++
                visited[r][c] = true
                val stack = ArrayList<IntArray>()
                stack.add(intArrayOf(r, c))
                while (stack.isNotEmpty()) {
                    val now = stack.removeAt(stack.size - 1)
                    for (d in 0 until 4) {
                        val nextR = now[0] + dr[d]
                        val nextC = now[1] + dc[d]
                        if (nextR < 0 || nextR >= rows || nextC < 0 || nextC >= cols) continue // 바닥 밖
                        if (floor[nextR][nextC] == '#' && !visited[nextR][nextC]) {
                            visited[nextR][nextC] = true
                            stack.add(intArrayOf(nextR, nextC))
                        }
                    }
                }
            }
        }
        return count
    }
}
