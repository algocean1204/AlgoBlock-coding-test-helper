#include <vector>
#include <set>
#include <algorithm>
#include <functional>

using namespace std;

vector<int> solution(int rows, vector<vector<int>> apples, int k) {
    vector<set<int>> kindsOf(rows + 1);  // kindsOf[줄 번호] = 그 줄의 서로 다른 무게(0번 칸은 쓰지 않는다)
    for (const auto& apple : apples) {
        kindsOf[apple[0]].insert(apple[1]);  // 같은 무게는 한 번만
    }

    vector<int> answer;
    for (int row = 1; row <= rows; row++) {
        vector<int> kinds(kindsOf[row].begin(), kindsOf[row].end());
        sort(kinds.begin(), kinds.end(), greater<int>());  // 무거운 것부터
        // k번째 무게는 위치 k-1. 적은 무게가 k개보다 적으면 -1(사과가 없는 줄 포함)
        answer.push_back(k <= (int) kinds.size() ? kinds[k - 1] : -1);
    }
    return answer;
}
