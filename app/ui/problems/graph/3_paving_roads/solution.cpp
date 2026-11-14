#include <string>
#include <vector>
#include <algorithm>

using namespace std;

// 재귀 대신 반복문: 긴 줄 입력에서 스택이 넘치지 않게
int find(vector<int>& parent, int x) {
    while (parent[x] != x) {
        parent[x] = parent[parent[x]]; // 경로 압축
        x = parent[x];
    }
    return x;
}

int solution(int n, vector<vector<int>> roads) {
    vector<int> parent(n + 1);
    for (int i = 0; i <= n; i++) parent[i] = i;

    // 싼 길부터 본다
    sort(roads.begin(), roads.end(), [](const vector<int>& p, const vector<int>& q) { return p[2] < q[2]; });

    long long total = 0; // 비용 합이 int를 넘을 수 있어 long long
    int paved = 0;
    for (auto& r : roads) {
        int rootA = find(parent, r[0]);
        int rootB = find(parent, r[1]);
        if (rootA == rootB) continue; // 이미 오갈 수 있다: 포장하면 고리가 생긴다
        parent[rootB] = rootA;
        total += r[2];
        paved++;
    }

    if (paved < n - 1) return -1; // 다 보고도 길이 n-1개가 안 되면 묶음이 둘 이상 남았다
    return (int)total;
}
