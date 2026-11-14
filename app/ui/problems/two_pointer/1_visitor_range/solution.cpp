#include <string>
#include <vector>

using namespace std;

vector<int> solution(vector<int> visitors, vector<vector<int>> queries) {
    // prefix[i]: 1일부터 i일까지 방문자 수의 합. prefix[0]은 아무 날도 더하지 않은 0
    // 합은 최대 10만 × 1만 = 10억이라 int에 들어간다
    vector<int> prefix(visitors.size() + 1, 0);
    for (size_t i = 0; i < visitors.size(); i++) {
        prefix[i + 1] = prefix[i] + visitors[i];
    }
    vector<int> answer;
    for (const vector<int>& query : queries) {
        int start = query[0];
        int end = query[1];
        answer.push_back(prefix[end] - prefix[start - 1]);
    }
    return answer;
}
