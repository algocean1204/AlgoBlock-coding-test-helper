class Solution {
    fun solution(log: Array<String>): IntArray {
        val count = HashMap<String, HashMap<String, Int>>()  // 구역 → {종 → 마릿수}. 1마리 이상인 종만 둔다
        val zonesOf = HashMap<String, Int>()  // 종 → 그 종이 1마리 이상 있는 구역 수
        val answers = ArrayList<Int>()
        for (line in log) {
            val words = line.split(" ")
            if (words[0] == "see") {
                val zone = words[1]
                val kind = words[2]
                val n = words[3].toInt()
                val inZone = count.getOrPut(zone) { HashMap() }
                val before = inZone[kind] ?: 0  // 덮어쓰기 전에 지금 값을 본다
                // 종의 구역 수는 없음 → 있음, 있음 → 없음으로 바뀔 때만 달라진다
                if (before == 0 && n > 0) {
                    zonesOf[kind] = (zonesOf[kind] ?: 0) + 1
                }
                if (before > 0 && n == 0) {
                    zonesOf[kind] = zonesOf[kind]!! - 1
                }
                if (n > 0) {
                    inZone[kind] = n  // 더하지 않고 바꾼다
                } else {
                    inZone.remove(kind)  // 0마리는 지운다: 구역의 종 수 = 안쪽 표의 크기
                }
            } else if (words[0] == "zone") {
                answers.add(count[words[1]]?.size ?: 0)
            } else {
                answers.add(zonesOf[words[1]] ?: 0)
            }
        }
        return answers.toIntArray()
    }
}
