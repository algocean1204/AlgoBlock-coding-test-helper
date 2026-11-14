#include <string>
#include <vector>
#include <queue>

using namespace std;

int solution(vector<string> records, int k) {
    // priority_queue는 기본이 최대 힙이라 가장 느린 기록(k위)이 꼭대기에 온다. 부호를 뒤집을 필요가 없다
    priority_queue<int> fastest;  // 지금까지 가장 빠른 기록 k개
    int alerts = 0;
    for (const string& record : records) {
        int minutes = stoi(record.substr(0, 2));
        int seconds = stoi(record.substr(3, 2));
        int time = minutes * 60 + seconds;
        if ((int)fastest.size() < k) {
            alerts++;
            fastest.push(time);
        } else if (time < fastest.top()) {  // 지금 k위보다 빨라야 한다. 같으면 먼저 들어온 기록이 앞선다
            alerts++;
            fastest.pop();
            fastest.push(time);
        }
    }
    return alerts;
}
