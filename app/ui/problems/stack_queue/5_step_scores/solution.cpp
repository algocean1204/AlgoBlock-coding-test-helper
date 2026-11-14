#include <string>
#include <vector>
#include <deque>

using namespace std;

long long solution(vector<int> scores, int jump) {
    int n = scores.size();
    vector<long long> best(n, 0); // best[i]: i번 돌에 섰을 때까지 모은 점수의 가장 큰 값. 합이 int를 넘을 수 있어 long long
    best[0] = scores[0];
    deque<int> window; // 바로 앞 jump개 돌의 번호. 앞에서 뒤로 갈수록 best가 작다
    window.push_back(0);
    for (int i = 1; i < n; i++) {
        // i번 돌로 한 번에 올 수 없는 돌(jump칸보다 먼 돌)은 앞에서 뺀다
        while (window.front() < i - jump) {
            window.pop_front();
        }
        best[i] = scores[i] + best[window.front()];
        // best[i]보다 작거나 같은 돌은 앞으로 고를 일이 없다: 뒤에서 버린다
        while (!window.empty() && best[window.back()] <= best[i]) {
            window.pop_back();
        }
        window.push_back(i);
    }
    return best[n - 1];
}
