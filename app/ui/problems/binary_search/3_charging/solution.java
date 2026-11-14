class Solution {
    public long solution(int n, int[] chargers) {
        int fastest = chargers[0];
        for (int minute : chargers) {
            fastest = Math.min(fastest, minute);
        }
        // 시간은 최대 100,000 x 500,000,000 = 5 x 10^13이라 int를 넘는다. 시간과 개수 합은 long으로 둔다
        long left = 1;
        long right = (long) fastest * n;
        while (left < right) {
            long mid = (left + right) / 2;
            long done = 0;
            for (int minute : chargers) {
                done += mid / minute;
            }
            if (done >= n) {
                right = mid;
            } else {
                left = mid + 1;
            }
        }
        return left;
    }
}
