class Solution {
    fun solution(heights: IntArray): IntArray {
        val n = heights.size
        val rests = IntArray(n)      // rests[j]: j번 지점에서 쉬는 등산객 수
        val walking = ArrayList<Int>() // 아직 쉴 곳을 찾지 못한 등산객의 출발 지점. 위로 갈수록 높다
        for (j in 0 until n) {
            // j번 지점이 맨 위 등산객의 출발 높이보다 낮거나 같으면, 그 등산객은 여기서 쉰다
            while (walking.isNotEmpty() && heights[walking[walking.size - 1]] >= heights[j]) {
                walking.removeAt(walking.size - 1)
                rests[j]++
            }
            walking.add(j) // j번 등산객이 걷기 시작한다
        }
        return rests // 끝까지 스택에 남은 등산객은 산책길을 벗어나 어디에도 세지 않는다
    }
}
