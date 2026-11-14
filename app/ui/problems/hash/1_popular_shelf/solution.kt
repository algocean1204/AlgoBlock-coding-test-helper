class Solution {
    fun solution(loans: Array<String>, k: Int): Array<String> {
        val count = HashMap<String, Int>()  // 제목마다 지금까지 빌려진 횟수
        val shelf = mutableListOf<String>()  // 추천 서가에 꽂힌 차례대로
        for (title in loans) {
            val now = count.getOrDefault(title, 0) + 1
            count[title] = now
            if (now == k) {  // 바로 지금 k번째로 빌려졌다
                shelf.add(title)
            }
        }
        return shelf.toTypedArray()
    }
}
