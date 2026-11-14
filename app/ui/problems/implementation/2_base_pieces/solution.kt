class Solution {
    fun solution(base: Int, reading: Long): LongArray {
        val digits = "0123456789ABCDEF"

        // 나머지를 끝 자리부터 모은 뒤 뒤집는다
        var rest = reading
        val reversed = StringBuilder()
        while (rest > 0) {
            reversed.append(digits[(rest % base).toInt()])
            rest /= base
        }
        val text = reversed.reverse().toString()

        // 앞 자리보다 작아지는 곳에서 새 조각을 시작한다
        val pieces = ArrayList<String>()
        pieces.add(text[0].toString())
        for (i in 1 until text.length) {
            if (digits.indexOf(text[i]) < digits.indexOf(text[i - 1])) {
                pieces.add(text[i].toString())
            } else {
                pieces[pieces.size - 1] = pieces[pieces.size - 1] + text[i]
            }
        }

        // 조각마다 앞자리부터 값 = 값 × base + 자리값으로 읽어 가장 큰 값을 고른다
        var largest = 0L
        for (piece in pieces) {
            var value = 0L
            for (ch in piece) {
                value = value * base + digits.indexOf(ch)
            }
            largest = maxOf(largest, value)
        }
        return longArrayOf(pieces.size.toLong(), largest)
    }
}
