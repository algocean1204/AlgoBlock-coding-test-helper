class Solution {
    fun solution(members: Int, roles: Int, auditions: Array<IntArray>, rivals: Array<IntArray>): Int {
        val n = members  // 단원 수
        val scores = Array(n) { IntArray(roles) }  // scores[단원][배역] = 오디션 점수. 0은 오디션을 보지 않아 맡을 수 없다는 뜻
        for (a in auditions) {
            scores[a[0]][a[1]] = a[2]
        }
        val rivalMask = IntArray(n)  // 함께 무대에 설 수 없는 단원들(비트, 양쪽에 모두 적는다)
        for (pair in rivals) {
            rivalMask[pair[0]] = rivalMask[pair[0]] or (1 shl pair[1])
            rivalMask[pair[1]] = rivalMask[pair[1]] or (1 shl pair[0])
        }
        // memo[몇 번 배역부터][누구를 썼는가(비트)] = 거기서 더 얻을 수 있는 가장 큰 점수. -2는 아직 모름
        val memo = Array(roles) { IntArray(1 shl n) { -2 } }

        // index번 배역부터 끝까지 정해서 더 얻을 수 있는 가장 큰 점수. 끝까지 정할 수 없으면 -1
        fun best(index: Int, used: Int): Int {
            if (index == roles) {
                return 0
            }
            if (memo[index][used] != -2) {  // 같은 상태에 다시 왔다: 기억한 값을 쓴다
                return memo[index][used]
            }
            var result = -1
            for (person in 0 until n) {
                if ((used shr person and 1) == 1 || scores[person][index] == 0) {
                    continue
                }
                if ((used and rivalMask[person]) != 0) {  // 이미 정한 단원과 부딪치면 이 가지는 버린다
                    continue
                }
                val rest = best(index + 1, used or (1 shl person))
                if (rest != -1) {  // 뒤의 배역을 끝까지 정할 수 있을 때만 후보가 된다
                    result = maxOf(result, scores[person][index] + rest)
                }
            }
            memo[index][used] = result
            return result
        }

        return best(0, 0)
    }
}
