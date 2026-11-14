#include <algorithm>
#include <queue>
#include <vector>

using namespace std;

vector<int> solution(int n, vector<vector<int>> cables, int start, vector<int> offline) {
    vector<vector<int>> neighbors(n + 1);
    for (auto& cable : cables) {
        neighbors[cable[0]].push_back(cable[1]); // 케이블은 양쪽 방향이다
        neighbors[cable[1]].push_back(cable[0]);
    }
    vector<bool> off(n + 1, false); // off[v]: v번 서버가 꺼져 있는가
    for (int server : offline) off[server] = true;

    // minute[v]: v번 서버가 파일을 받는 시각. -1은 아직(또는 끝내) 받지 못한 서버
    vector<int> minute(n + 1, -1);
    minute[start] = 0;
    queue<int> q;
    q.push(start);
    while (!q.empty()) {
        int server = q.front();
        q.pop();
        for (int next : neighbors[server]) {
            if (minute[next] == -1 && !off[next]) { // 꺼진 서버는 받지도 보내지도 않는다
                minute[next] = minute[server] + 1;
                q.push(next);
            }
        }
    }
    // start번 서버가 0분이라 받지 못한 서버(-1)는 가장 큰 값이 되지 않는다
    int latest = *max_element(minute.begin(), minute.end());
    return {latest, (int)count(minute.begin(), minute.end(), latest)};
}
