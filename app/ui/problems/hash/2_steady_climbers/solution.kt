class Solution {
    fun solution(names: Array<String>, days: IntArray, limit: Int): Int {
        val last = HashMap<String, Int>()  // 손님 → 마지막으로 온 날
        val visits = HashMap<String, Int>()  // 손님 → 서로 다른 날에 온 횟수
        val broken = HashSet<String>()  // 이웃한 두 날의 차이가 limit을 넘은 적이 있는 손님
        for (i in names.indices) {
            val name = names[i]
            val day = days[i]
            val before = last[name]
            if (before == null) {  // 처음 온 손님
                last[name] = day
                visits[name] = 1
            } else if (day != before) {  // 같은 날 다시 들어온 것은 새 방문이 아니다
                if (day - before > limit) {
                    broken.add(name)
                }
                last[name] = day  // 이제 이 날이 마지막으로 온 날이다
                visits[name] = visits[name]!! + 1
            }
        }

        var steady = 0
        for ((name, count) in visits) {
            if (count >= 2 && name !in broken) {
                steady++
            }
        }
        return steady
    }
}
