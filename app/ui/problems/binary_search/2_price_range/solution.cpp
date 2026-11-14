#include <string>
#include <vector>
#include <algorithm>

using namespace std;

// values에서 x 이상인 값이 처음 나오는 자리(없으면 길이)
int firstAtLeast(const vector<int>& values, int x) {
    int left = 0;
    int right = (int)values.size();
    while (left < right) {
        int mid = (left + right) / 2;
        if (values[mid] >= x) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    return left;
}

vector<int> solution(vector<int> prices, vector<vector<int>> ranges) {
    sort(prices.begin(), prices.end());
    vector<int> answer;
    for (const vector<int>& r : ranges) {
        int low = r[0];
        int high = r[1];
        int start = firstAtLeast(prices, low);
        // 가격이 정수라서 'high보다 큰 값이 처음 나오는 자리' = 'high + 1 이상이 처음 나오는 자리'
        int end = firstAtLeast(prices, high + 1);
        answer.push_back(end - start);
    }
    return answer;
}
