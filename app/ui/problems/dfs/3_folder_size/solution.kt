// 재귀로 쓰면 폴더가 10만 겹일 때 스택이 넘친다. 그래서 바깥에서 안쪽으로 방문한 순서를 스택으로 구하고
// 그 순서를 거꾸로 따라가며 더한다(안쪽이 먼저 끝난다).
class Solution {
    fun solution(parent: IntArray, files: IntArray, limit: Int): Int {
        val n = parent.size
        val children = Array(n) { ArrayList<Int>() }
        for (folder in 0 until n) {
            if (parent[folder] != -1) children[parent[folder]].add(folder)
        }
        // 0번에서 출발해 바깥에서 안쪽으로 방문한 순서를 적는다(재귀 대신 스택)
        val order = IntArray(n)
        var size = 0
        val stack = ArrayList<Int>()
        stack.add(0)
        while (stack.isNotEmpty()) {
            val folder = stack.removeAt(stack.size - 1)
            order[size++] = folder
            for (child in children[folder]) stack.add(child)
        }
        // 이 순서를 거꾸로 보면 안쪽 폴더가 언제나 바깥 폴더보다 먼저 나온다.
        // 전체 용량은 최대 10억이라 Int에 들어간다
        val total = files.clone()
        for (i in n - 1 downTo 0) {
            val folder = order[i]
            if (parent[folder] != -1) total[parent[folder]] += total[folder]
        }
        var count = 0
        for (t in total) if (t >= limit) count++
        return count
    }
}
