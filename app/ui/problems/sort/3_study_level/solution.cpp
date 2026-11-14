#include <string>
#include <vector>
#include <algorithm>

using namespace std;

int solution(vector<int> solved) {
    sort(solved.begin(), solved.end(), greater<int>()); // 많이 푼 회원부터
    int level = 0;
    for (int i = 0; i < (int)solved.size(); i++) {
        // 앞에서 i+1명은 모두 solved[i]문제 이상 풀었다.
        // 그러니 solved[i] >= i+1이면 'i+1문제 이상 푼 회원이 i+1명 이상'이 된다
        if (solved[i] >= i + 1) {
            level = i + 1;
        } else {
            break; // 여기서 안 되면 더 큰 x도 안 된다
        }
    }
    return level;
}
