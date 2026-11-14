class Solution {
    // 순열 도구가 없어서 재귀로 직접 만든다: 안 쓴 타일을 하나씩 뒤에 붙여 가며 모든 순서를 본다
    private fun build(tiles: String, used: BooleanArray, number: Int, length: Int, numbers: MutableSet<Int>) {
        if (length >= 2) {
            numbers.add(number) // 같은 수는 집합이 한 번만 남긴다
        }
        for (i in tiles.indices) {
            if (used[i]) continue
            if (length == 0 && tiles[i] == '0') continue // 맨 앞에 0 타일은 놓을 수 없다
            used[i] = true
            // 최대 8자리라 Int로 충분하다
            build(tiles, used, number * 10 + (tiles[i] - '0'), length + 1, numbers)
            used[i] = false
        }
    }

    fun solution(tiles: String, m: Int): Int {
        val numbers = HashSet<Int>()
        build(tiles, BooleanArray(tiles.length), 0, 0, numbers)
        var count = 0
        for (x in numbers) {
            if (x % m == 0) {
                count++
            }
        }
        return count
    }
}
