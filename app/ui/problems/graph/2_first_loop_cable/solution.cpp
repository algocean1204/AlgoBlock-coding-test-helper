#include <string>
#include <vector>
#include <unordered_map>

using namespace std;

// 재귀 대신 반복문: 긴 줄 입력에서 스택이 넘치지 않게
string find(unordered_map<string, string>& parent, string x) {
    if (!parent.count(x)) parent[x] = x;
    while (parent[x] != x) {
        parent[x] = parent[parent[x]]; // 경로 압축
        x = parent[x];
    }
    return x;
}

int solution(vector<vector<string>> cables) {
    unordered_map<string, string> parent; // 정점이 이름(문자열)이라 맵을 쓴다

    for (int i = 0; i < (int)cables.size(); i++) {
        string rootX = find(parent, cables[i][0]);
        string rootY = find(parent, cables[i][1]);
        if (rootX == rootY) {
            return i + 1; // 몇 번째 케이블인지는 1부터 센다
        }
        parent[rootY] = rootX;
    }
    return -1;
}
