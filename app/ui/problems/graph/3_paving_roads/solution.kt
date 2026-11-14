class Solution {
    // 재귀 대신 반복문: 긴 줄 입력에서 스택이 넘치지 않게
    private fun find(parent: IntArray, start: Int): Int {
        var x = start
        while (parent[x] != x) {
            parent[x] = parent[parent[x]] // 경로 압축
            x = parent[x]
        }
        return x
    }

    fun solution(n: Int, roads: Array<IntArray>): Int {
        val parent = IntArray(n + 1) { it }

        val sorted = roads.sortedBy { it[2] } // 싼 길부터 본다

        var total = 0L // 비용 합이 Int를 넘을 수 있어 Long
        var paved = 0
        for (r in sorted) {
            val rootA = find(parent, r[0])
            val rootB = find(parent, r[1])
            if (rootA == rootB) continue // 이미 오갈 수 있다: 포장하면 고리가 생긴다
            parent[rootB] = rootA
            total += r[2]
            paved++
        }

        if (paved < n - 1) return -1 // 다 보고도 길이 n-1개가 안 되면 묶음이 둘 이상 남았다
        return total.toInt()
    }
}
