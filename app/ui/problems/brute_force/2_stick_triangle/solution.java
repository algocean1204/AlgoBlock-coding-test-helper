class Solution {
    public int solution(int[] sticks) {
        int count = 0;
        int n = sticks.length;
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                for (int k = j + 1; k < n; k++) {
                    // 세 막대 중 가장 긴 것과 나머지 둘의 합을 비교한다. 합은 long으로 계산해 넘침을 막는다
                    long a = sticks[i], b = sticks[j], c = sticks[k];
                    long longest = Math.max(a, Math.max(b, c));
                    long sum = a + b + c - longest; // 가장 긴 것을 뺀 두 막대의 합
                    if (longest < sum) {
                        count++;
                    }
                }
            }
        }
        return count;
    }
}
