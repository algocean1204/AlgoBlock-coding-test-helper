import java.util.*;

class Solution {
    public int solution(int[] taste, int[] look) {
        int n = taste.length;
        int[][] people = new int[n][];
        for (int i = 0; i < n; i++) {
            people[i] = new int[]{taste[i], look[i]};
        }
        // 맛 점수가 높은 사람부터 본다. 맛 점수가 같으면 모양 점수가 낮은 사람부터 본다.
        // 같은 맛 점수끼리는 서로 떨어뜨리지 못하므로, 같은 무리에서 모양 점수가 높은 사람이
        // 먼저 지나가 bestLook을 올려 두면 안 된다.
        Arrays.sort(people, (a, b) -> {
            if (a[0] != b[0]) return Integer.compare(b[0], a[0]); // 맛은 내림차순
            return Integer.compare(a[1], b[1]); // 모양은 오름차순
        });

        int bestLook = -1; // 지금까지 지나간 사람들의 모양 점수 가운데 가장 높은 값
        int count = 0;
        for (int[] p : people) {
            int myLook = p[1];
            // 앞에 지나간 사람은 나보다 맛 점수가 높거나, 같은 맛 점수에 모양 점수가 나 이하다.
            // 그러니 bestLook이 내 모양 점수보다 높으면, 맛도 모양도 나보다 높은 사람이 있다는 뜻이다.
            if (bestLook <= myLook) {
                count++;
            }
            bestLook = Math.max(bestLook, myLook);
        }
        return count;
    }
}
