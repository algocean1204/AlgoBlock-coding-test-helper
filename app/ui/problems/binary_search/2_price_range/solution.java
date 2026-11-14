import java.util.Arrays;

class Solution {
    // values에서 x 이상인 값이 처음 나오는 자리(없으면 길이)
    private int firstAtLeast(int[] values, int x) {
        int left = 0;
        int right = values.length;
        while (left < right) {
            int mid = (left + right) / 2;
            if (values[mid] >= x) {
                right = mid;
            } else {
                left = mid + 1;
            }
        }
        return left;
    }

    public int[] solution(int[] prices, int[][] ranges) {
        int[] sorted = prices.clone();
        Arrays.sort(sorted);
        int[] answer = new int[ranges.length];
        for (int i = 0; i < ranges.length; i++) {
            int low = ranges[i][0];
            int high = ranges[i][1];
            int start = firstAtLeast(sorted, low);
            // 가격이 정수라서 'high보다 큰 값이 처음 나오는 자리' = 'high + 1 이상이 처음 나오는 자리'
            // (high는 10억 이하라 high + 1이 int 안에 든다)
            int end = firstAtLeast(sorted, high + 1);
            answer[i] = end - start;
        }
        return answer;
    }
}
