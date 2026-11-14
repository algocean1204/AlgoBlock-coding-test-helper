import java.util.*;

// 재귀로 쓰면 쉼터가 5만 개 한 줄일 때 스택이 넘친다. 그래서 재귀 대신,
// '들어갈 때'와 '돌아올 때'를 스택에 따로 넣어 같은 순서를 만든다(돌아올 때는 -번호-1로 구분한다).
class Solution {
    public int solution(int[][] trails, int[] energy, int target) {
        int n = energy.length;
        List<List<Integer>> neighbors = new ArrayList<>();
        for (int i = 0; i < n; i++) neighbors.add(new ArrayList<>());
        for (int[] trail : trails) {
            neighbors.get(trail[0]).add(trail[1]); // 어느 쪽이 위쪽인지 모르므로 양쪽에 넣는다
            neighbors.get(trail[1]).add(trail[0]);
        }
        int[] prefix = new int[n]; // prefix[v]: 0번부터 v번까지 길 위 energy의 합(최대 5천만이라 int로 충분하다)
        prefix[0] = energy[0];
        // 지금 경로 위의 누적 합이 몇 번씩 있는가. 0번 위(아무 쉼터도 지나지 않은 곳)의 누적 합 0을 넣어 둔다
        Map<Integer, Integer> onPath = new HashMap<>();
        onPath.put(0, 1);
        boolean[] visited = new boolean[n];
        visited[0] = true;
        int count = 0; // 코스 수는 최대 n(n+1)/2 = 약 12.5억이라 int에 들어간다
        ArrayDeque<Integer> stack = new ArrayDeque<>();
        stack.push(0);
        while (!stack.isEmpty()) {
            int top = stack.pop();
            if (top < 0) {
                int hut = -top - 1;
                onPath.merge(prefix[hut], -1, Integer::sum); // 이 쉼터 아래를 다 보았다: 경로에서 뺀다
                continue;
            }
            int hut = top;
            // u부터 hut까지의 합 = prefix[hut] - (u 바로 위까지의 누적 합). 그 값이 target인 u의 수를 더한다
            count += onPath.getOrDefault(prefix[hut] - target, 0);
            onPath.merge(prefix[hut], 1, Integer::sum);
            stack.push(-hut - 1); // 아래쪽을 다 본 뒤에 꺼내지도록 먼저 넣는다
            for (int next : neighbors.get(hut)) {
                if (!visited[next]) {
                    visited[next] = true;
                    prefix[next] = prefix[hut] + energy[next];
                    stack.push(next);
                }
            }
        }
        return count;
    }
}
