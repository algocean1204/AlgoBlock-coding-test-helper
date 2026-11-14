#include <string>
#include <vector>
#include <queue>
#include <functional>

using namespace std;

long long solution(vector<int> snowballs) {
    // priority_queue는 기본이 최대 힙이다. greater를 주면 가장 작은 것이 꼭대기인 최소 힙이 된다
    // 합이 int를 넘을 수 있어 long long으로 담는다
    priority_queue<long long, vector<long long>, greater<long long>> heap;
    for (int snowball : snowballs) {
        heap.push(snowball);
    }
    long long total = 0;
    while (heap.size() > 1) {
        long long lightest = heap.top();
        heap.pop();
        long long second = heap.top();
        heap.pop();
        long long merged = lightest + second;
        total += merged;
        heap.push(merged);
    }
    return total;
}
