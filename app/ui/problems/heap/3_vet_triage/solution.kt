import java.util.PriorityQueue

class Solution {
    fun solution(patients: Array<IntArray>): Long {
        val n = patients.size
        // 원소는 {도착 시각, 진료 시간, 위급도, 번호}. 도착 시각 순으로 정렬한다
        val arrivals = Array(n) { intArrayOf(patients[it][0], patients[it][1], patients[it][2], it) }
        arrivals.sortBy { it[0] }
        // 도착한 동물: 위급도는 큰 것(부호를 뒤집어 비교), 진료 시간은 짧은 것, 번호는 작은 것이 꼭대기에 온다
        val waiting = PriorityQueue<IntArray>(compareBy({ -it[2] }, { it[1] }, { it[3] }))
        var time = 0
        var nextArrival = 0 // arrivals에서 아직 힙에 넣지 않은 첫 자리
        var total = 0L      // 기다린 시간의 합은 Int를 넘을 수 있다
        repeat(n) {
            if (waiting.isEmpty() && arrivals[nextArrival][0] > time) {
                time = arrivals[nextArrival][0] // 도착한 동물이 없으면 다음 동물이 올 때까지 건너뛴다
            }
            while (nextArrival < n && arrivals[nextArrival][0] <= time) {
                waiting.add(arrivals[nextArrival])
                nextArrival++
            }
            val pet = waiting.poll()
            total += (time - pet[0]).toLong()
            time += pet[1]
        }
        return total
    }
}
