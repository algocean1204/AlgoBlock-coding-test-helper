class Solution {
    public long solution(int n) {
        // 탑의 수는 int 범위를 넘으므로 long으로 담는다
        long[] ways = new long[n + 1];  // ways[h]: 높이가 정확히 h인 탑의 수
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
