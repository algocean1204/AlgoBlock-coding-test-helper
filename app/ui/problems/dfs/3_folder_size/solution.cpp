#include <vector>

using namespace std;

// 재귀로 쓰면 폴더가 10만 겹일 때 스택이 넘칠 수 있다. 그래서 바깥에서 안쪽으로 방문한 순서를 스택으로 구하고
// 그 순서를 거꾸로 따라가며 더한다(안쪽이 먼저 끝난다).
int solution(vector<int> parent, vector<int> files, int limit) {
    int n = parent.size();
    vector<vector<int>> children(n);
    for (int folder = 0; folder < n; folder++) {
        if (parent[folder] != -1) children[parent[folder]].push_back(folder);
    }
    // 0번에서 출발해 바깥에서 안쪽으로 방문한 순서를 적는다(재귀 대신 스택)
    vector<int> order;
    vector<int> stack = {0};
    while (!stack.empty()) {
        int folder = stack.back();
        stack.pop_back();
        order.push_back(folder);
        for (int child : children[folder]) stack.push_back(child);
    }
    // 이 순서를 거꾸로 보면 안쪽 폴더가 언제나 바깥 폴더보다 먼저 나온다.
    // 전체 용량은 최대 10억이라 int에 들어간다
    vector<int> total = files;
    for (int i = n - 1; i >= 0; i--) {
        int folder = order[i];
        if (parent[folder] != -1) total[parent[folder]] += total[folder];
    }
    int count = 0;
    for (int size : total) if (size >= limit) count++;
    return count;
}
