class Solution {
    fun solution(records: Array<String>): Array<String> {
        // 첫 번째 훑기: 메시지마다 마지막 상태(보낸이, 마지막 내용, 고친 적 있는가, 지워졌는가)를 모은다
        val order = ArrayList<String>()
        val sender = HashMap<String, String>()
        val text = HashMap<String, String>()
        val edited = HashSet<String>()
        val deleted = HashSet<String>()
        for (record in records) {
            val words = record.split(" ")
            val number = words[1]
            if (words[0] == "SEND") {
                order.add(number)
                sender[number] = words[2]
                text[number] = words[3]
            } else if (words[0] == "EDIT") {
                text[number] = words[2]
                edited.add(number)
            } else {
                deleted.add(number)
            }
        }

        // 두 번째 훑기: 남은 메시지를 보낸 순서대로 보며, 바로 앞 줄과 보낸이가 같으면 그 줄에 붙인다
        val lines = ArrayList<StringBuilder>()
        var lineSender = ""
        for (number in order) {
            if (number in deleted) {
                continue
            }
            val shown = text[number]!! + (if (number in edited) "*" else "")
            if (lines.isNotEmpty() && lineSender == sender[number]) {
                lines[lines.size - 1].append(" ").append(shown)
            } else {
                lines.add(StringBuilder(sender[number]!! + ": " + shown))
                lineSender = sender[number]!!
            }
        }
        return lines.map { it.toString() }.toTypedArray()
    }
}
