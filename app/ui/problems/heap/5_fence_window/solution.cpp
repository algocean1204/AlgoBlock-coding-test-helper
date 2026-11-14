#include <string>
#include <vector>
#include <queue>
#include <functional>
#include <utility>

using namespace std;

// 규칙 하나: 꼭대기를 보거나 꺼내기 전에는 언제나 이것을 부른다.
// 꼭대기에 창 밖으로 나간 판자(번호 < left)가 있으면 버린다. 힙 안쪽에 있는 것은 꼭대기에 올라올 때 버린다
template <typename Heap>
void dropOld(Heap& heap, int left) {
    while (!heap.empty() && heap.top().second < left) {
        heap.pop();
    }
}

vector<long long> solution(vector<int> heights, int w) {
    int n = heights.size();
    // 원소는 {높이, 번호}. priority_queue는 기본이 최대 힙이다
    // low: 작은 쪽 절반. 기본 최대 힙 그대로 쓰면 높이가 가장 큰 판자가 꼭대기에 온다. 부호를 뒤집을 필요가 없다
    priority_queue<pair<int, int>> low;
    // high: 큰 쪽 절반. greater를 줘서 높이가 가장 낮은 판자가 꼭대기에 오게 한다
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<pair<int, int>>> high;
    vector<bool> inLow(n, false);  // 판자마다 지금 low에 들어 있는지
    int lowCount = 0;              // 창 안에 남은 판자 수. 지울 표시만 한 판자가 힙에 남아 있어 size()와 다르다
    int highCount = 0;
    long long lowSum = 0;          // 합은 int를 넘을 수 있어 long long
    long long highSum = 0;
    int left = 0;                  // 창의 맨 왼쪽 번호. 이보다 작은 번호는 창 밖이다
    vector<long long> costs;
    for (int right = 0; right < n; right++) {
        int height = heights[right];
        // 1. 새 판자를 넣는다(4단계와 같다)
        dropOld(low, left);
        if (low.empty() || height <= low.top().first) {
            low.push({height, right});
            inLow[right] = true;
            lowCount++;
            lowSum += height;
        } else {
            high.push({height, right});
            highCount++;
            highSum += height;
        }
        // 2. 창이 w개를 넘으면 맨 왼쪽 판자를 뺀다. 힙에서 바로 지우지 않고 개수와 합에서만 뺀다
        if (right - left + 1 > w) {
            if (inLow[left]) {
                lowCount--;
                lowSum -= heights[left];
            } else {
                highCount--;
                highSum -= heights[left];
            }
            left++;
        }
        // 3. 개수 맞추기: lowCount가 highCount와 같거나 하나 더 많게. 옮기기 전에 꼭대기의 나간 판자를 버린다
        while (lowCount > highCount + 1) {
            dropOld(low, left);
            auto moved = low.top();
            low.pop();
            high.push(moved);
            inLow[moved.second] = false;
            lowCount--;
            lowSum -= moved.first;
            highCount++;
            highSum += moved.first;
        }
        while (highCount > lowCount) {
            dropOld(high, left);
            auto moved = high.top();
            high.pop();
            low.push(moved);
            inLow[moved.second] = true;
            highCount--;
            highSum -= moved.first;
            lowCount++;
            lowSum += moved.first;
        }
        // 4. 창이 w개로 찼으면 가운데 높이(low의 꼭대기)로 맞추는 비용을 잰다
        if (right - left + 1 == w) {
            dropOld(low, left);
            long long middle = low.top().first;
            costs.push_back((middle * lowCount - lowSum) + (highSum - middle * highCount));
        }
    }
    return costs;
}
