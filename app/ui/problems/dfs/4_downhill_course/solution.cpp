#include <unordered_map>
#include <vector>

using namespace std;

// 재귀로 쓰면 쉼터가 5만 개 한 줄일 때 스택이 넘칠 수 있다. 그래서 재귀 대신,
// '들어갈 때'와 '돌아올 때'를 스택에 따로 넣어 같은 순서를 만든다(돌아올 때는 -번호-1로 구분한다).
int solution(vector<vector<int>> trails, vector<int> energy, int target) {
    int n = energy.size();
    vector<vector<int>> neighbors(n);
    for (auto& trail : trails) {
        neighbors[trail[0]].push_back(trail[1]); // 어느 쪽이 위쪽인지 모르므로 양쪽에 넣는다
        neighbors[trail[1]].push_back(trail[0]);
    }
    vector<int> prefix(n, 0); // prefix[v]: 0번부터 v번까지 길 위 energy의 합(최대 5천만이라 int로 충분하다)
    prefix[0] = energy[0];
    // 지금 경로 위의 누적 합이 몇 번씩 있는가. 0번 위(아무 쉼터도 지나지 않은 곳)의 누적 합 0을 넣어 둔다
    unordered_map<int, int> onPath;
    onPath[0] = 1;
    vector<bool> visited(n, false);
    visited[0] = true;
    int count = 0; // 코스 수는 최대 n(n+1)/2 = 약 12.5억이라 int에 들어간다
    vector<int> stack = {0};
    while (!stack.empty()) {
        int top = stack.back();
        stack.pop_back();
        if (top < 0) {
            int hut = -top - 1;
            onPath[prefix[hut]]--; // 이 쉼터 아래를 다 보았다: 경로에서 뺀다
            continue;
        }
        int hut = top;
        // u부터 hut까지의 합 = prefix[hut] - (u 바로 위까지의 누적 합). 그 값이 target인 u의 수를 더한다
        auto found = onPath.find(prefix[hut] - target);
        if (found != onPath.end()) count += found->second;
        onPath[prefix[hut]]++;
        stack.push_back(-hut - 1); // 아래쪽을 다 본 뒤에 꺼내지도록 먼저 넣는다
        for (int next : neighbors[hut]) {
            if (!visited[next]) {
                visited[next] = true;
                prefix[next] = prefix[hut] + energy[next];
                stack.push_back(next);
            }
        }
    }
    return count;
}
