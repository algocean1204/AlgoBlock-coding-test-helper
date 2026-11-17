// 언어 함정: java.int_overflow @ "탑의 수는 2,147,483,647보다 클 수 있습니다"
class Solution {
    public long solution(int n) {
        int[] ways = new int[n + 1];  // ways[h]: 높이가 정확히 h인 탑의 수
        ways[0] = 1;  // 아무것도 쌓지 않은 높이 0의 탑 하나
        for (int height = 1; height <= n; height++) {
            for (int block = 1; block <= 3; block++) {  // 맨 위에 놓은 블록의 높이
                if (height - block >= 0) {
                    ways[height] += ways[height - block];
                }
            }
        }
        return ways[n];
    }
}
