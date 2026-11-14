class Solution {
    fun solution(board: Array<String>): Long {
        val rows = board.size
        val cols = board[0].length
        val NEW = 0 // 아직 안 감
        val ON_PATH = 1 // 지금 걷는 길 위
        val DONE = 2 // 점수가 정해짐
        val state = Array(rows) { IntArray(cols) { NEW } }
        val order = Array(rows) { IntArray(cols) } // 지금 길에서 몇 번째로 밟은 칸인가
        val score = Array(rows) { IntArray(cols) }
        val path = IntArray(rows * cols) // 한 번만 만들어 계속 다시 쓴다. 칸 번호 = 행 * cols + 열
        for (startR in 0 until rows) {
            for (startC in 0 until cols) {
                if (state[startR][startC] == DONE) continue
                // 1. 밖으로 나가거나, 점수가 정해진 칸에 닿거나, 지금 길 위의 칸에 다시 닿을 때까지 걸으며 길을 적는다
                var size = 0
                var r = startR
                var c = startC
                var nextScore: Int
                while (true) {
                    state[r][c] = ON_PATH
                    order[r][c] = size
                    path[size++] = r * cols + c
                    when (board[r][c]) {
                        'U' -> r--
                        'D' -> r++
                        'L' -> c--
                        else -> c++
                    }
                    if (r < 0 || r >= rows || c < 0 || c >= cols) {
                        nextScore = 0 // 밖이다: 더 밟을 칸이 없다
                        break
                    }
                    if (state[r][c] == DONE) {
                        nextScore = score[r][c] // 답을 아는 칸: 더 걷지 않고 이어 쓴다
                        break
                    }
                    if (state[r][c] == ON_PATH) {
                        // 고리: 다시 닿은 칸부터 지금 칸까지. 고리 위의 칸은 어디서 출발하든 고리를 한 바퀴 돈다
                        val first = order[r][c]
                        val length = size - first
                        for (i in first until size) {
                            score[path[i] / cols][path[i] % cols] = length
                            state[path[i] / cols][path[i] % cols] = DONE
                        }
                        size = first // 남은 것은 고리로 들어가기 전의 칸들
                        nextScore = length
                        break
                    }
                }
                // 2. 걸어온 길을 거꾸로 돌아오며 '다음 칸의 점수 + 1'을 적는다
                for (i in size - 1 downTo 0) {
                    nextScore++
                    score[path[i] / cols][path[i] % cols] = nextScore
                    state[path[i] / cols][path[i] % cols] = DONE
                }
            }
        }
        var total = 0L // 합은 최대 약 6백억이라 Long이 필요하다
        for (row in score) for (s in row) total += s
        return total
    }
}
