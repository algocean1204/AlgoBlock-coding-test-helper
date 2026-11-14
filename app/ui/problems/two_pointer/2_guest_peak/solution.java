class Solution {
    public int solution(int days, int[][] bookings) {
        // diff[d]: d일에 새로 늘어나는(음수면 줄어드는) 손님 수. last + 1일 = days + 1일까지 쓰므로 days + 2칸
        int[] diff = new int[days + 2];
        for (int[] booking : bookings) {
            int first = booking[0];
            int last = booking[1];
            int guests = booking[2];
            diff[first] += guests;
            diff[last + 1] -= guests;
        }
        // 1일부터 누적하면 그날 묵는 사람 수가 된다 (최대 5만 × 1,000 = 5천만이라 int로 충분)
        int best = 0;
        int staying = 0;
        for (int day = 1; day <= days; day++) {
            staying += diff[day];
            best = Math.max(best, staying);
        }
        return best;
    }
}
