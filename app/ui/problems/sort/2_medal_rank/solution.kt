class Solution {
    fun solution(classes: Array<String>, medals: Array<IntArray>): Array<String> {
        // 반 번호(0..n-1)를 줄 세운다. 정렬 기준은 금 많은 순 → 은 많은 순 → 동 많은 순 → 이름 사전 순
        val order = classes.indices.sortedWith(Comparator { a, b ->
            // 메달은 많은 쪽이 앞(내림차순)이라 b와 a의 자리를 바꿔 비교한다
            if (medals[a][0] != medals[b][0]) return@Comparator medals[b][0].compareTo(medals[a][0])
            if (medals[a][1] != medals[b][1]) return@Comparator medals[b][1].compareTo(medals[a][1])
            if (medals[a][2] != medals[b][2]) return@Comparator medals[b][2].compareTo(medals[a][2])
            classes[a].compareTo(classes[b]) // 이름은 사전 순(오름차순). 소문자뿐이라 compareTo가 곧 사전 순이다
        })
        return Array(classes.size) { classes[order[it]] }
    }
}
