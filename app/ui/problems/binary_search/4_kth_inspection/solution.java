class Solution {
    // day일까지(그날 포함) 이루어진 점검 수. 모두 400억 번까지라 long으로 센다
    private long countUntil(int[][] schedules, long day) {
        long total = 0;
        for (int[] s : schedules) {
            long first = s[0], gap = s[1], times = s[2];
            if (day >= first) {  // 첫 점검 전이면 0번
                total += Math.min(times, (day - first) / gap + 1);  // times번을 넘지 않는다
            }
        }
        return total;
    }

    public long solution(int[][] schedules, long k) {
        long left = Long.MAX_VALUE, right = 0;
        for (int[] s : schedules) {
            left = Math.min(left, (long) s[0]);
            right = Math.max(right, s[0] + (long) (s[2] - 1) * s[1]);
        }
        // 그날까지의 점검이 k번 이상인 가장 이른 날을 찾는다
        while (left < right) {
            long mid = (left + right) / 2;
            if (countUntil(schedules, mid) >= k) {
                right = mid;
            } else {
                left = mid + 1;
            }
        }
        return left;
    }
}
