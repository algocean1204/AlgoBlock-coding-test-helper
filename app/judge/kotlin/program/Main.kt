fun main() {
    val count = readln().toInt()
    var total = 0
    repeat(count) {
        total += readln().toInt()
    }
    println(total)
}
