// 언어 함정: cpp.int_multiply @ "n은 1 이상 500,000,000 이하" "chargers의 원소는 1 이상 100,000 이하"
#include <string>
#include <vector>
#include <algorithm>

using namespace std;

long long solution(int n, vector<int> chargers) {
    int fastest = *min_element(chargers.begin(), chargers.end());
    // 시간은 최대 5 x 10^13이라 int를 넘는다. 시간과 개수 합은 long long으로 둔다
    long long left = 1;
    long long right = fastest * n;
    while (left < right) {
        long long mid = (left + right) / 2;
        long long done = 0;
        for (int minute : chargers) {
            done += mid / minute;
        }
        if (done >= n) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    return left;
}
