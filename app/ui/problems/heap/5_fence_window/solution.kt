import java.util.PriorityQueue

class Solution {
    // 규칙 하나: 꼭대기를 보거나 꺼내기 전에는 언제나 이것을 부른다.
    // 꼭대기에 창 밖으로 나간 판자(번호 < left)가 있으면 버린다. 힙 안쪽에 있는 것은 꼭대기에 올라올 때 버린다
    private fun dropOld(heap: PriorityQueue<IntArray>, left: Int) {
        while (heap.isNotEmpty() && heap.peek()[1] < left) {
            heap.poll()
        }
    }

    fun solution(heights: IntArray, w: Int): LongArray {
        val n = heights.size
        // 원소는 intArrayOf(높이, 번호). PriorityQueue는 최소 힙이라 비교 기준을 줘서 방향을 정한다
        // low: 작은 쪽 절반. 높이가 큰 판자가 꼭대기에 오게 비교한다(부호를 뒤집는 대신 기준을 거꾸로)
        val low = PriorityQueue<IntArray>(compareBy<IntArray>({ -it[0] }, { it[1] }))
        // high: 큰 쪽 절반. 높이가 낮은 판자가 꼭대기에 온다
        val high = PriorityQueue<IntArray>(compareBy<IntArray>({ it[0] }, { it[1] }))
        val inLow = BooleanArray(n) // 판자마다 지금 low에 들어 있는지
        var lowCount = 0            // 창 안에 남은 판자 수. 지울 표시만 한 판자가 힙에 남아 있어 size와 다르다
        var highCount = 0
        var lowSum = 0L             // 합은 Int를 넘을 수 있어 Long
        var highSum = 0L
        var left = 0                // 창의 맨 왼쪽 번호. 이보다 작은 번호는 창 밖이다
        val costs = LongArray(n - w + 1)
        var filled = 0
        for (right in 0 until n) {
            val height = heights[right]
            // 1. 새 판자를 넣는다(4단계와 같다)
            dropOld(low, left)
            if (low.isEmpty() || height <= low.peek()[0]) {
                low.add(intArrayOf(height, right))
                inLow[right] = true
                lowCount++
                lowSum += height
            } else {
                high.add(intArrayOf(height, right))
                highCount++
                highSum += height
            }
            // 2. 창이 w개를 넘으면 맨 왼쪽 판자를 뺀다. 힙에서 바로 지우지 않고 개수와 합에서만 뺀다
            if (right - left + 1 > w) {
                if (inLow[left]) {
                    lowCount--
                    lowSum -= heights[left]
                } else {
                    highCount--
                    highSum -= heights[left]
                }
                left++
            }
            // 3. 개수 맞추기: lowCount가 highCount와 같거나 하나 더 많게. 옮기기 전에 꼭대기의 나간 판자를 버린다
            while (lowCount > highCount + 1) {
                dropOld(low, left)
                val moved = low.poll()
                high.add(moved)
                inLow[moved[1]] = false
                lowCount--
                lowSum -= moved[0]
                highCount++
                highSum += moved[0]
            }
            while (highCount > lowCount) {
                dropOld(high, left)
                val moved = high.poll()
                low.add(moved)
                inLow[moved[1]] = true
                highCount--
                highSum -= moved[0]
                lowCount++
                lowSum += moved[0]
            }
            // 4. 창이 w개로 찼으면 가운데 높이(low의 꼭대기)로 맞추는 비용을 잰다
            if (right - left + 1 == w) {
                dropOld(low, left)
                val middle = low.peek()[0].toLong()
                costs[filled++] = (middle * lowCount - lowSum) + (highSum - middle * highCount)
            }
        }
        return costs
    }
}
