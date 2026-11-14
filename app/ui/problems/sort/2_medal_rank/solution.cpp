#include <string>
#include <vector>
#include <algorithm>

using namespace std;

vector<string> solution(vector<string> classes, vector<vector<int>> medals) {
    int n = classes.size();
    // 반 번호(0..n-1)를 줄 세운다. 정렬 기준은 금 많은 순 → 은 많은 순 → 동 많은 순 → 이름 사전 순
    vector<int> order(n);
    for (int i = 0; i < n; i++) order[i] = i;
    sort(order.begin(), order.end(), [&](int a, int b) {
        // 메달은 많은 쪽이 앞(내림차순)이라 > 로 비교한다
        if (medals[a][0] != medals[b][0]) return medals[a][0] > medals[b][0];
        if (medals[a][1] != medals[b][1]) return medals[a][1] > medals[b][1];
        if (medals[a][2] != medals[b][2]) return medals[a][2] > medals[b][2];
        return classes[a] < classes[b]; // 이름은 사전 순(오름차순). 앞이어야 true
    });
    vector<string> answer;
    for (int i : order) answer.push_back(classes[i]);
    return answer;
}
