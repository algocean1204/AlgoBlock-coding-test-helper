import java.util.ArrayDeque

class Solution {
    fun solution(start: String, goal: String, dictionary: Array<String>): Int {
        val words = HashSet<String>(dictionary.asList())
        if (!words.contains(goal)) return -1

        // steps: start에서 낱말을 만들기까지 바꾼 횟수. 들어 있으면 이미 큐에 넣은 낱말이다
        val steps = HashMap<String, Int>()
        steps[start] = 0
        val queue = ArrayDeque<String>()
        queue.add(start)
        while (queue.isNotEmpty()) {
            val word = queue.poll()
            if (word == goal) return steps[word]!!
            val chars = word.toCharArray()
            for (i in chars.indices) {
                val original = chars[i]
                for (ch in 'a'..'z') {
                    if (ch == original) continue
                    chars[i] = ch // 한 자리만 바꾼 이웃 후보를 직접 만든다
                    val candidate = String(chars)
                    if (words.contains(candidate) && !steps.containsKey(candidate)) {
                        steps[candidate] = steps[word]!! + 1
                        queue.add(candidate)
                    }
                }
                chars[i] = original
            }
        }
        return -1
    }
}
