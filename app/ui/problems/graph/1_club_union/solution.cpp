#include <string>
#include <vector>

using namespace std;

int solution(int n, vector<vector<int>> merges) {
    vector<int> parent(n + 1);
    for (int i = 0; i <= n; i++) parent[i] = i;

    // find를 재귀로 쓰면 긴 줄 입력에서 스택이 넘치므로 반복문으로 쓴다
    auto find = [&](int x) {
        while (parent[x] != x) {
            parent[x] = parent[parent[x]]; // 경로 압축: 한 칸 위를 건너뛰어 대표에 가깝게 고쳐 둔다
            x = parent[x];
        }
        return x;
    };

    int groups = n;
    for (auto& m : merges) {
        int rootA = find(m[0]);
        int rootB = find(m[1]);
        if (rootA != rootB) {
            parent[rootB] = rootA;
            groups--;
        }
    }
    return groups;
}
