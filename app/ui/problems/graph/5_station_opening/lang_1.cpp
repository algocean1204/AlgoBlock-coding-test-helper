// 언어 함정: cpp.int_overflow
#include <string>
#include <vector>

using namespace std;

vector<int> solution(int n, vector<vector<int>> tracks, vector<vector<int>> queries) {
    const int INF = 2147483647; // int에서 가장 큰 값
    vector<vector<int>> dist(n + 1, vector<int>(n + 1, INF));
    for (int s = 1; s <= n; s++) dist[s][s] = 0;
    for (auto& t : tracks) {
        if (t[2] < dist[t[0]][t[1]]) { // 같은 두 역 사이 선로가 여럿이면 짧은 것만 남긴다
            dist[t[0]][t[1]] = t[2];
            dist[t[1]][t[0]] = t[2];
        }
    }

    vector<vector<int>> asked(n + 1); // asked[k]: k번 역까지 열렸을 때를 묻는 질문의 번호들
    for (int i = 0; i < (int)queries.size(); i++) asked[queries[i][0]].push_back(i);

    vector<int> answer(queries.size(), 0);
    for (int k = 1; k <= n; k++) {
        // 플로이드: k번 역을 거쳐 가는 길로 모든 두 역 사이 거리를 고친다(아직 닫힌 역까지의 거리도 고쳐 둔다)
        for (int i = 1; i <= n; i++) {
            for (int j = 1; j <= n; j++) {
                if (dist[i][k] + dist[k][j] < dist[i][j]) {
                    dist[i][j] = dist[i][k] + dist[k][j];
                }
            }
        }
        // 이제 dist[a][b]는 1~k번 역만 거쳐 가는 가장 짧은 시간이다
        for (int idx : asked[k]) {
            long long d = dist[queries[idx][1]][queries[idx][2]];
            answer[idx] = d >= INF ? -1 : (int)d;
        }
    }
    return answer;
}
