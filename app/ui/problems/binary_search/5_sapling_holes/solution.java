import java.util.Arrays;

class Solution {
    // 모든 간격을 gap 이상으로 둘 때 심을 수 있는 묘목의 수
    private int planted(int[] trees, int[] holes, int gap) {
        int count = 0;
        int last = -1_000_000_000;  // 지금 보는 구덩이 바로 앞에 있는 나무(없으면 아주 먼 곳)
        int i = 0;  // trees[i]: 지금 보는 구덩이 뒤에 오는 첫 큰 나무
        for (int hole : holes) {
            while (i < trees.length && trees[i] < hole) {  // 구덩이보다 앞에 있는 큰 나무를 지나간다
                last = trees[i];
                i++;
            }
            int nextTree = i < trees.length ? trees[i] : 2_000_000_000;  // 뒤에 큰 나무가 없으면 아주 먼 곳
            // 앞 나무와도, 뒤에 오는 큰 나무와도 gap 이상 떨어져야 심는다
            if (hole - last >= gap && nextTree - hole >= gap) {
                count++;
                last = hole;
            }
        }
        return count;
    }

    public int solution(int[] trees, int[] holes, int count) {
        int[] sortedTrees = trees.clone();
        int[] sortedHoles = holes.clone();
        Arrays.sort(sortedTrees);
        Arrays.sort(sortedHoles);
        int left = 1;
        int right = Math.max(sortedTrees[sortedTrees.length - 1], sortedHoles[sortedHoles.length - 1])
                - Math.min(sortedTrees[0], sortedHoles[0]);
        for (int i = 0; i + 1 < sortedTrees.length; i++) {  // 큰 나무끼리의 간격은 바꿀 수 없으므로 답은 이보다 클 수 없다
            right = Math.min(right, sortedTrees[i + 1] - sortedTrees[i]);
        }
        int answer = 1;
        while (left <= right) {
            int mid = left + (right - left) / 2;
            if (planted(sortedTrees, sortedHoles, mid) >= count) {  // 더 많이 심을 수 있으면 몇 그루를 덜 심으면 된다
                answer = mid;
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }
        return answer;
    }
}
