// 언어 함정: cpp.int_overflow @ "houses의 길이는 1 이상 100,000 이하" "1일째부터 마지막 날까지 모두 더한 값"
#include <string>
#include <vector>
#include <queue>
#include <functional>

using namespace std;

long long solution(vector<int> houses) {
    // priority_queue는 기본이 최대 힙이라 low는 그대로 쓰면 가장 큰 값이 꼭대기에 온다. 부호를 뒤집을 필요가 없다
    priority_queue<long long> low;                                          // 작은 쪽 절반
    priority_queue<long long, vector<long long>, greater<long long>> high;  // 큰 쪽 절반. greater를 줘서 가장 작은 값이 꼭대기에 온다
    // 거리 합은 int를 넘을 수 있어 모두 long long으로 둔다
    long long lowSum = 0;
    long long highSum = 0;
    int total = 0;
    for (int house : houses) {
        if (low.empty() || house <= low.top()) {
            low.push(house);
            lowSum += house;
        } else {
            high.push(house);
            highSum += house;
        }
        // 개수 맞추기: low가 high와 같거나 하나 더 많게 둔다. 그러면 low의 꼭대기가 가운데 값이다
        if (low.size() > high.size() + 1) {
            long long moved = low.top();
            low.pop();
            lowSum -= moved;
            high.push(moved);
            highSum += moved;
        } else if (high.size() > low.size()) {
            long long moved = high.top();
            high.pop();
            highSum -= moved;
            low.push(moved);
            lowSum += moved;
        }
        long long middle = low.top();
        // (작은 쪽 집들에서 가운데까지의 거리 합) + (큰 쪽 집들에서 가운데까지의 거리 합)
        total += (middle * (long long)low.size() - lowSum) + (highSum - middle * (long long)high.size());
    }
    return total;
}
