class Solution {
    fun solution(title: String, taken: Array<String>): String {
        val skip = listOf("a", "an", "the", "of", "and")

        // 1~2. 빈칸으로 나누고, 낱말마다 소문자로 바꿔 영문 소문자·숫자만 남긴다. 다 지워진 낱말은 뺀다
        var words = ArrayList<String>()
        for (word in title.split(" ")) {
            val kept = StringBuilder()
            for (ch in word.lowercase()) {
                if (ch in 'a'..'z' || ch in '0'..'9') {
                    kept.append(ch)
                }
            }
            if (kept.isNotEmpty()) {
                words.add(kept.toString())
            }
        }

        // 3. 규칙 3의 낱말 빼기. 다 빠져 목록이 비면 빼지 않는다
        val left = ArrayList<String>()
        for (word in words) {
            if (word !in skip) {
                left.add(word)
            }
        }
        if (left.isNotEmpty()) {
            words = left
        }

        // 4. 낱말 단위로 이어 붙이다가 길이가 24를 넘게 되면 멈춘다
        var slug = words[0].take(24)
        for (i in 1 until words.size) {
            if (slug.length + 1 + words[i].length > 24) {
                break
            }
            slug = slug + "-" + words[i]
        }

        // 5. taken에 있으면 -2, -3, … 을 붙여 본다
        val used = taken.toHashSet()
        if (slug !in used) {
            return slug
        }
        var number = 2
        while ((slug + "-" + number) in used) {
            number++
        }
        return slug + "-" + number
    }
}
