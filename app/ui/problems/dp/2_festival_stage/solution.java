class Solution {
    public int solution(int[] pay) {
        int n = pay.length;
        if (n == 1) {
            return pay[0];
        }
        // 길이가 10만이라 재귀 대신 반복문으로 앞에서부터 채운다
        int[] best = new int[n];  // best[i]: 0 ~ i번째 날만 보고 골랐을 때 사례금 합의 최댓값
        best[0] = pay[0];
        best[1] = Math.max(pay[0], pay[1]);
        for (int i = 2; i < n; i++) {
            int rest = best[i - 1];  // i번째 날은 쉰다
            int perform = best[i - 2] + pay[i];  // i번째 날 공연한다: 바로 앞날은 쉬었어야 한다
            best[i] = Math.max(rest, perform);
        }
        return best[n - 1];
    }
}
