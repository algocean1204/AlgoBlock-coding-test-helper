#include <string>
#include <vector>
#include <algorithm>

using namespace std;

// 모든 간격을 gap 이상으로 둘 때 심을 수 있는 묘목의 수
int planted(const vector<int>& trees, const vector<int>& holes, int gap) {
    int count = 0;
    int last = -1000000000;  // 지금 보는 구덩이 바로 앞에 있는 나무(없으면 아주 먼 곳)
    size_t i = 0;  // trees[i]: 지금 보는 구덩이 뒤에 오는 첫 큰 나무
    for (int hole : holes) {
        while (i < trees.size() && trees[i] < hole) {  // 구덩이보다 앞에 있는 큰 나무를 지나간다
            last = trees[i];
            i++;
        }
        int nextTree = i < trees.size() ? trees[i] : 2000000000;  // 뒤에 큰 나무가 없으면 아주 먼 곳
        // 앞 나무와도, 뒤에 오는 큰 나무와도 gap 이상 떨어져야 심는다
        if (hole - last >= gap && nextTree - hole >= gap) {
            count++;
            last = hole;
        }
    }
    return count;
}

int solution(vector<int> trees, vector<int> holes, int count) {
    sort(trees.begin(), trees.end());
    sort(holes.begin(), holes.end());
    int left = 1;
    int right = max(trees.back(), holes.back()) - min(trees.front(), holes.front());
    for (size_t i = 0; i + 1 < trees.size(); i++) {  // 큰 나무끼리의 간격은 바꿀 수 없으므로 답은 이보다 클 수 없다
        right = min(right, trees[i + 1] - trees[i]);
    }
    int answer = 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (planted(trees, holes, mid) >= count) {  // 더 많이 심을 수 있으면 몇 그루를 덜 심으면 된다
            answer = mid;
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    return answer;
}
