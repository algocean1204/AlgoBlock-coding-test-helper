import java.util.ArrayDeque;

class Solution {
    public int solution(int[] arrive, int ride, int gap, int cap) {
        ArrayDeque<Integer> sliding = new ArrayDeque<>(); // 미끄럼틀 안에 있는 사람이 벗어나는 시각. 먼저 출발한 사람이 앞
        int nextPerson = 0;    // 줄의 맨 앞 사람 번호
        int lastStart = -1;    // 바로 앞사람이 출발한 시각(아직 아무도 출발하지 않았으면 -1)
        int total = 0;
        int time = 0;
        while (nextPerson < arrive.length) {
            while (!sliding.isEmpty() && sliding.peekFirst() == time) { // 먼저 벗어난다
                sliding.pollFirst();
            }
            boolean arrived = arrive[nextPerson] <= time;
            boolean room = sliding.size() < cap;
            boolean gapPassed = lastStart == -1 || time - lastStart >= gap;
            if (arrived && room && gapPassed) { // 그다음 맨 앞 사람 한 명이 출발한다
                sliding.addLast(time + ride);
                total += time - arrive[nextPerson];
                lastStart = time;
                nextPerson++;
            }
            time++;
        }
        return total;
    }
}
