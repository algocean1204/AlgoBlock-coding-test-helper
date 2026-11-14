class Solution {
    // 재귀 대신 반복문: 긴 줄 입력에서 스택이 넘치지 않게
    private fun find(parent: HashMap<String, String>, start: String): String {
        var x = start
        if (!parent.containsKey(x)) parent[x] = x
        while (parent[x] != x) {
            parent[x] = parent[parent[x]!!]!! // 경로 압축
            x = parent[x]!!
        }
        return x
    }

    fun solution(cables: Array<Array<String>>): Int {
        val parent = HashMap<String, String>() // 정점이 이름(문자열)이라 맵을 쓴다

        for ((i, c) in cables.withIndex()) {
            val rootX = find(parent, c[0])
            val rootY = find(parent, c[1])
            if (rootX == rootY) {
                return i + 1 // 몇 번째 케이블인지는 1부터 센다
            }
            parent[rootY] = rootX
        }
        return -1
    }
}
