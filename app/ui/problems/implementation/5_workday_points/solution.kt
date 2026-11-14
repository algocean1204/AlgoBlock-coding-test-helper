import java.util.TreeMap

class Solution {
    private val monthDays = intArrayOf(31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    private val yearStart = LongArray(10000)

    private fun isLeap(year: Int): Boolean {
        if (year % 400 == 0) return true
        if (year % 100 == 0) return false
        return year % 4 == 0
    }

    private fun dayNumber(date: String): Long {
        // "YYYY-MM-DD" → 1년 1월 1일이 0, 그다음 날이 1, …
        val year = date.substring(0, 4).toInt()
        val month = date.substring(5, 7).toInt()
        val day = date.substring(8, 10).toInt()
        var number = yearStart[year]
        for (m in 1 until month) {  // 그해에 지나간 달의 날 수
            number += monthDays[m - 1]
            if (m == 2 && isLeap(year)) {
                number += 1
            }
        }
        return number + day - 1
    }

    private fun weekdays(first: Long, last: Long): Long {
        // first일째부터 last일째까지(둘 다 셈) 평일 수. 0일째가 월요일이므로 (일 번호 % 7) < 5이면 평일
        val total = last - first + 1
        val weeks = total / 7
        var count = weeks * 5  // 7일 묶음마다 평일 5일. 점수 합이 약 1,300억이라 Long
        var number = first + weeks * 7  // 남은 6일 이하는 하나씩 본다
        while (number <= last) {
            if (number % 7 < 5) {
                count++
            }
            number++
        }
        return count
    }

    fun solution(staff: Array<Array<String>>, today: String): LongArray {
        // 해마다 '1년 1월 1일부터 그해 1월 1일까지 며칠인가'를 한 번만 구해 둔다
        var days = 0L
        for (year in 1 until 10000) {
            yearStart[year] = days
            days += if (isLeap(year)) 366 else 365
        }

        val todayNumber = dayNumber(today)
        val points = TreeMap<String, Long>()  // TreeMap은 부서 이름을 사전 순으로 꺼낸다
        for (row in staff) {
            val last = if (row[2] == "-") todayNumber else dayNumber(row[2])
            points[row[0]] = (points[row[0]] ?: 0L) + weekdays(dayNumber(row[1]), last)
        }
        return points.values.toLongArray()
    }
}
