// 언어 함정: java.int_overflow @ "heights의 원소는 1 이상 500,000,000 이하"
import java.util.PriorityQueue;

class Solution {
    // 규칙 하나: 꼭대기를 보거나 꺼내기 전에는 언제나 이것을 부른다.
    // 꼭대기에 창 밖으로 나간 판자(번호 < left)가 있으면 버린다. 힙 안쪽에 있는 것은 꼭대기에 올라올 때 버린다
    private void dropOld(PriorityQueue<int[]> heap, int left) {
        while (!heap.isEmpty() && heap.peek()[1] < left) {
            heap.poll();
        }
    }

    public long[] solution(int[] heights, int w) {
        int n = heights.length;
        // 원소는 {높이, 번호}. PriorityQueue는 최소 힙이라 비교 기준을 줘서 방향을 정한다
        // low: 작은 쪽 절반. 높이가 큰 판자가 꼭대기에 오게 비교한다(부호를 뒤집는 대신 기준을 거꾸로)
        PriorityQueue<int[]> low = new PriorityQueue<>((a, b) -> {
            if (a[0] != b[0]) return Integer.compare(b[0], a[0]);
            return Integer.compare(a[1], b[1]);
        });
        // high: 큰 쪽 절반. 높이가 낮은 판자가 꼭대기에 온다
        PriorityQueue<int[]> high = new PriorityQueue<>((a, b) -> {
            if (a[0] != b[0]) return Integer.compare(a[0], b[0]);
            return Integer.compare(a[1], b[1]);
        });
        boolean[] inLow = new boolean[n]; // 판자마다 지금 low에 들어 있는지
        int lowCount = 0;                 // 창 안에 남은 판자 수. 지울 표시만 한 판자가 힙에 남아 있어 size()와 다르다
        int highCount = 0;
        int lowSum = 0;                   // 작은 쪽 높이의 합
        long highSum = 0L;
        int left = 0;                     // 창의 맨 왼쪽 번호. 이보다 작은 번호는 창 밖이다
        long[] costs = new long[n - w + 1];
        int filled = 0;
        for (int right = 0; right < n; right++) {
            int height = heights[right];
            // 1. 새 판자를 넣는다(4단계와 같다)
            dropOld(low, left);
            if (low.isEmpty() || height <= low.peek()[0]) {
                low.add(new int[]{height, right});
                inLow[right] = true;
                lowCount++;
                lowSum += height;
            } else {
                high.add(new int[]{height, right});
                highCount++;
                highSum += height;
            }
            // 2. 창이 w개를 넘으면 맨 왼쪽 판자를 뺀다. 힙에서 바로 지우지 않고 개수와 합에서만 뺀다
            if (right - left + 1 > w) {
                if (inLow[left]) {
                    lowCount--;
                    lowSum -= heights[left];
                } else {
                    highCount--;
                    highSum -= heights[left];
                }
                left++;
            }
            // 3. 개수 맞추기: lowCount가 highCount와 같거나 하나 더 많게. 옮기기 전에 꼭대기의 나간 판자를 버린다
            while (lowCount > highCount + 1) {
                dropOld(low, left);
                int[] moved = low.poll();
                high.add(moved);
                inLow[moved[1]] = false;
                lowCount--;
                lowSum -= moved[0];
                highCount++;
                highSum += moved[0];
            }
            while (highCount > lowCount) {
                dropOld(high, left);
                int[] moved = high.poll();
                low.add(moved);
                inLow[moved[1]] = true;
                highCount--;
                highSum -= moved[0];
                lowCount++;
                lowSum += moved[0];
            }
            // 4. 창이 w개로 찼으면 가운데 높이(low의 꼭대기)로 맞추는 비용을 잰다
            if (right - left + 1 == w) {
                dropOld(low, left);
                long middle = low.peek()[0];
                costs[filled++] = (middle * lowCount - lowSum) + (highSum - middle * highCount);
            }
        }
        return costs;
    }
}
