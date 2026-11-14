import java.util.*;

// 재귀로 쓰면 폴더가 10만 겹일 때 스택이 넘친다. 그래서 바깥에서 안쪽으로 방문한 순서를 스택으로 구하고
// 그 순서를 거꾸로 따라가며 더한다(안쪽이 먼저 끝난다).
class Solution {
    public int solution(int[] parent, int[] files, int limit) {
        int n = parent.length;
        List<List<Integer>> children = new ArrayList<>();
        for (int i = 0; i < n; i++) children.add(new ArrayList<>());
        for (int folder = 0; folder < n; folder++) {
            if (parent[folder] != -1) children.get(parent[folder]).add(folder);
        }
        // 0번에서 출발해 바깥에서 안쪽으로 방문한 순서를 적는다(재귀 대신 스택)
        int[] order = new int[n];
        int size = 0;
        ArrayDeque<Integer> stack = new ArrayDeque<>();
        stack.push(0);
        while (!stack.isEmpty()) {
            int folder = stack.pop();
            order[size++] = folder;
            for (int child : children.get(folder)) stack.push(child);
        }
        // 이 순서를 거꾸로 보면 안쪽 폴더가 언제나 바깥 폴더보다 먼저 나온다.
        // 전체 용량은 최대 10만 × 10,000 = 10억이라 int에 들어간다
        int[] total = files.clone();
        for (int i = n - 1; i >= 0; i--) {
            int folder = order[i];
            if (parent[folder] != -1) total[parent[folder]] += total[folder];
        }
        int count = 0;
        for (int t : total) if (t >= limit) count++;
        return count;
    }
}
