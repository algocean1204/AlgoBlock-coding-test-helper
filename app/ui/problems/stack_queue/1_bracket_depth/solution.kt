class Solution {
    fun solution(expr: String): Int {
        val stack = ArrayDeque<Char>()
        var deepest = 0
        for (ch in expr) {
            if (ch == '(' || ch == '[' || ch == '{') {
                stack.addLast(ch)
                deepest = maxOf(deepest, stack.size)
            } else if (ch == ')' || ch == ']' || ch == '}') {
                val open = if (ch == ')') '(' else if (ch == ']') '[' else '{'
                if (stack.isEmpty() || stack.last() != open) {
                    return -1
                }
                stack.removeLast()
            }
        }
        if (stack.isNotEmpty()) {
            return -1
        }
        return deepest
    }
}
