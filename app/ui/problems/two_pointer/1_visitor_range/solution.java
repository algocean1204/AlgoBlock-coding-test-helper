class Solution {
    public int[] solution(int[] visitors, int[][] queries) {
        // prefix[i]: 1일부터 i일까지 방문자 수의 합. prefix[0]은 아무 날도 더하지 않은 0
        // 합은 최대 10만 × 1만 = 10억이라 int에 들어간다
        int[] prefix = new int[visitors.length + 1];
        for (int i = 0; i < visitors.length; i++) {
            prefix[i + 1] = prefix[i] + visitors[i];
        }
        int[] answer = new int[queries.length];
        for (int q = 0; q < queries.length; q++) {
            int start = queries[q][0];
            int end = queries[q][1];
            answer[q] = prefix[end] - prefix[start - 1];
        }
        return answer;
    }
}
