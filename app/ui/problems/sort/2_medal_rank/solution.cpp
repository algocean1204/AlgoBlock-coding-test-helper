#include <algorithm>
#include <string>
#include <tuple>
#include <vector>

using namespace std;

vector<string> solution(vector<string> classes, vector<vector<int>> medals) {
    vector<tuple<int, int, int, string>> rows;
    for (int i = 0; i < (int)classes.size(); i++) {
        int gold = medals[i][0], silver = medals[i][1], bronze = medals[i][2];
        // 메달은 많은 쪽이 앞(내림차순)이라 마이너스를 붙이고, 이름은 사전 순(오름차순) 그대로 둔다
        rows.push_back({-gold, -silver, -bronze, classes[i]});
    }
    sort(rows.begin(), rows.end()); // tuple은 앞 기준부터 비교하고, 같으면 다음 기준으로 넘어간다
    vector<string> answer;
    for (const auto& row : rows) answer.push_back(get<3>(row));
    return answer;
}
