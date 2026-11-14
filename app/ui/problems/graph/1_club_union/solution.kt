class Solution {
    // find를 재귀로 쓰면 긴 줄 입력에서 스택이 넘치므로 반복문으로 쓴다
    private fun find(parent: IntArray, start: Int): Int {
        var x = start
        while (parent[x] != x) {
            parent[x] = parent[parent[x]] // 경로 압축: 한 칸 위를 건너뛰어 대표에 가깝게 고쳐 둔다
            x = parent[x]
        }
        return x
    }

    fun solution(n: Int, merges: Array<IntArray>): Int {
        val parent = IntArray(n + 1) { it }

        var groups = n
        for (m in merges) {
            val rootA = find(parent, m[0])
            val rootB = find(parent, m[1])
            if (rootA != rootB) {
                parent[rootB] = rootA
                groups--
            }
        }
        return groups
    }
}
