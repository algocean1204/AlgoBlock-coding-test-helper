import java.util.Arrays;

class Solution {
    public int solution(int[] sticks) {
        int count = 0;
        int n = sticks.length;
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                for (int k = j + 1; k < n; k++) {
                    int[] three = {sticks[i], sticks[j], sticks[k]};
                    Arrays.sort(three); // 작은 것부터 늘어놓으면 마지막이 가장 긴 막대다
                    int shortest = three[0], middle = three[1], longest = three[2];
                    if (longest < shortest + middle) {
                        count++;
                    }
                }
            }
        }
        return count;
    }
}
